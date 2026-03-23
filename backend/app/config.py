from pydantic_settings import BaseSettings


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
    frontend_url: str = "http://localhost:3000"
    admin_password: str = "admin"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
