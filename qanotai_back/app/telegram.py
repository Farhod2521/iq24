import httpx

from .config import get_settings

_bot_username: str | None = None


async def bot_username() -> str:
    """The bot's @username, looked up once via getMe so it never has to be configured separately."""
    global _bot_username
    if _bot_username is None:
        token = get_settings().telegram_bot_token
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        r.raise_for_status()
        _bot_username = r.json()["result"]["username"]
    return _bot_username
