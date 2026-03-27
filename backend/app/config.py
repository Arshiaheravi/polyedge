from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./polyedge.db"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_basic_price_id: str = ""
    stripe_vip_price_id: str = ""
    telegram_bot_token: str = ""
    telegram_bot_username: str = "PolyEdgeBot"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""  # e.g. +15005550006
    frontend_url: str = "http://localhost:8003"  # FastAPI serves the SPA at /
    admin_password: str = "admin"
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_claims_email: str = "admin@polyedge.com"
    vip_poll_interval_seconds: int = 5
    default_poll_interval_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origins(self) -> list[str]:
        """Explicit CORS allowlist derived from the configured frontend URL.

        Credentialed CORS cannot use a wildcard, so we allow the frontend origin
        plus its localhost/127.0.0.1 equivalent for local development.
        """
        origins = {self.frontend_url.rstrip("/")}
        origins.add("http://localhost:3000")
        origins.add("http://127.0.0.1:3000")
        return sorted(origins)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
