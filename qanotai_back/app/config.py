from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://qanot:qanot@localhost:5432/qanot"

    # signs the session cookie — must be a long random string in production
    jwt_secret: str = "change-me"
    jwt_expire_days: int = 30
    cookie_secure: bool = False  # True behind https

    # where the site is opened in the browser; Google redirects back here (through the Next.js /api proxy)
    public_url: str = "http://localhost:3000"

    telegram_bot_token: str = ""
    telegram_login_ttl_seconds: int = 300

    google_client_id: str = ""
    google_client_secret: str = ""

    # comma-separated; these accounts get the /superadmin panel
    superadmin_telegram_ids: str = ""
    superadmin_emails: str = ""

    # ── AI test generator ── any provider: base URL + key + model
    # format: "openai" (OpenAI-style /chat/completions — most providers) or "anthropic" (Claude /v1/messages)
    ai_url: str = ""
    ai_key: str = ""
    ai_model: str = ""
    ai_format: str = "openai"

    # uploaded files (book covers); served at /api/media
    media_dir: str = "media"

    @property
    def superadmin_telegram_id_set(self) -> set[int]:
        return {int(x) for x in self.superadmin_telegram_ids.replace(" ", "").split(",") if x}

    @property
    def superadmin_email_set(self) -> set[str]:
        return {x.strip().lower() for x in self.superadmin_emails.split(",") if x.strip()}

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.public_url.rstrip('/')}/api/auth/google/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
