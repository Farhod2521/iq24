import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..models import TelegramLogin, User
from ..security import clear_session_cookie, current_user, is_superadmin, set_session_cookie
from ..telegram import bot_username

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str | None
    phone: str | None
    avatar_url: str | None
    telegram_username: str | None
    has_google: bool
    has_telegram: bool
    plan: str
    is_superadmin: bool
    created_at: datetime

    @classmethod
    def of(cls, u: User) -> "UserOut":
        return cls(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            avatar_url=u.avatar_url,
            telegram_username=u.telegram_username,
            has_google=u.google_sub is not None,
            has_telegram=u.telegram_id is not None,
            plan=u.plan,
            is_superadmin=is_superadmin(u),
            created_at=u.created_at,
        )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.of(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    clear_session_cookie(response)


# ─── Telegram ────────────────────────────────────────────────────────────────


class TelegramStartOut(BaseModel):
    token: str
    url: str
    expires_in: int


class TelegramStatusOut(BaseModel):
    status: str  # pending | confirmed | rejected | expired | used


def _device(request: Request) -> str:
    ua = request.headers.get("user-agent", "")
    browser = next((b for b in ("Edg", "OPR", "Chrome", "Firefox", "Safari") if b in ua), "Brauzer")
    browser = {"Edg": "Edge", "OPR": "Opera"}.get(browser, browser)
    os_name = next((o for o in ("Windows", "Android", "iPhone", "iPad", "Mac OS", "Linux") if o in ua), "")
    return f"{browser}, {os_name}".strip(", ")[:120]


@router.post("/telegram/start", response_model=TelegramStartOut)
async def telegram_start(request: Request, session: AsyncSession = Depends(get_session)) -> TelegramStartOut:
    s = get_settings()
    if not s.telegram_bot_token:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Telegram bot sozlanmagan")
    try:
        username = await bot_username()
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Telegram bilan bog'lanib bo'lmadi")

    token = secrets.token_urlsafe(24)  # [A-Za-z0-9_-], fits Telegram's 64-char /start payload
    session.add(
        TelegramLogin(
            token=token,
            device=_device(request),
            expires_at=datetime.now(UTC) + timedelta(seconds=s.telegram_login_ttl_seconds),
        )
    )
    await session.commit()
    return TelegramStartOut(
        token=token, url=f"https://t.me/{username}?start={token}", expires_in=s.telegram_login_ttl_seconds
    )


@router.get("/telegram/status/{token}", response_model=TelegramStatusOut)
async def telegram_status(token: str, response: Response, session: AsyncSession = Depends(get_session)) -> TelegramStatusOut:
    login = await session.get(TelegramLogin, token)
    if login is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "So'rov topilmadi")

    if login.status == "confirmed":
        # hand the session out exactly once, even if two polls race
        claimed = await session.execute(
            update(TelegramLogin)
            .where(TelegramLogin.token == token, TelegramLogin.status == "confirmed")
            .values(status="used")
            .returning(TelegramLogin.user_id)
        )
        user_id = claimed.scalar_one_or_none()
        await session.commit()
        if user_id is None:
            return TelegramStatusOut(status="used")
        set_session_cookie(response, user_id)
        return TelegramStatusOut(status="confirmed")

    if login.status == "pending" and login.expires_at < datetime.now(UTC):
        return TelegramStatusOut(status="expired")
    return TelegramStatusOut(status=login.status)


# ─── Google (OAuth 2.0 authorization-code flow) ──────────────────────────────

GOOGLE_STATE_COOKIE = "g_oauth_state"


def _home_with_error(code: str) -> RedirectResponse:
    return RedirectResponse(f"{get_settings().public_url}/?login=1&login_error={code}", status.HTTP_303_SEE_OTHER)


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    s = get_settings()
    if not (s.google_client_id and s.google_client_secret):
        return _home_with_error("google_not_configured")

    state = secrets.token_urlsafe(24)
    params = {
        "client_id": s.google_client_id,
        "redirect_uri": s.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    response = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")
    response.set_cookie(
        GOOGLE_STATE_COOKIE, state, max_age=600, httponly=True, secure=s.cookie_secure, samesite="lax", path="/"
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    s = get_settings()
    expected = request.cookies.get(GOOGLE_STATE_COOKIE)
    if not code or not state or not expected or not secrets.compare_digest(state, expected):
        return _home_with_error("google")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            tok = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": s.google_client_id,
                    "client_secret": s.google_client_secret,
                    "redirect_uri": s.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            tok.raise_for_status()
            info = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {tok.json()['access_token']}"},
            )
            info.raise_for_status()
    except (httpx.HTTPError, KeyError):
        return _home_with_error("google")

    g = info.json()
    email = g.get("email") if g.get("email_verified") else None

    # same Google account → same user; a verified email already on file links the account
    conditions = [User.google_sub == g["sub"]] + ([User.email == email] if email else [])
    user = (await session.execute(select(User).where(or_(*conditions)))).scalars().first()
    if user is None:
        user = User(full_name=g.get("name") or email or "Foydalanuvchi")
        session.add(user)
    user.google_sub = g["sub"]
    user.email = user.email or email
    user.avatar_url = g.get("picture") or user.avatar_url
    user.last_login_at = datetime.now(UTC)
    await session.commit()

    response = RedirectResponse(f"{s.public_url}/dashboard", status.HTTP_303_SEE_OTHER)
    response.delete_cookie(GOOGLE_STATE_COOKIE, path="/")
    set_session_cookie(response, user.id)
    return response
