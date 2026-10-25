from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .models import User

SESSION_COOKIE = "qanot_session"


def set_session_cookie(response: Response, user_id: int) -> None:
    s = get_settings()
    expires = datetime.now(UTC) + timedelta(days=s.jwt_expire_days)
    token = jwt.encode({"sub": str(user_id), "exp": expires}, s.jwt_secret, algorithm="HS256")
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=s.jwt_expire_days * 86400,
        httponly=True,
        secure=s.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


async def current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tizimga kirilmagan")
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        user = await session.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        user = None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessiya yaroqsiz")
    return user


def is_superadmin(user: User) -> bool:
    s = get_settings()
    return (user.telegram_id is not None and user.telegram_id in s.superadmin_telegram_id_set) or (
        user.email is not None and user.email.lower() in s.superadmin_email_set
    )


async def require_superadmin(user: User = Depends(current_user)) -> User:
    if not is_superadmin(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    return user
