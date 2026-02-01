"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # Authentication
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    JWT_ALGORITHM: str = "HS256"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5-mini"

    # Email Provider Selection
    EMAIL_PROVIDER: str = "postmark"  # "postmark" or "resend"
    EMAIL_FROM_ADDRESS: str = ""  # Unified from address (falls back to FROM_EMAIL)
    EMAIL_FROM_NAME: str = "Outreach AI"  # Unified from name
    
    # Postmark (used when EMAIL_PROVIDER=postmark)
    POSTMARK_SERVER_TOKEN: str = ""
    POSTMARK_INBOUND_ADDRESS: str = ""
    FROM_EMAIL: str = ""  # Legacy, use EMAIL_FROM_ADDRESS instead
    FROM_NAME: str = "Outreach AI"  # Legacy, use EMAIL_FROM_NAME instead
    
    # Resend (used when EMAIL_PROVIDER=resend)
    RESEND_API_KEY: str = ""
    
    # Reply Mode
    REPLY_MODE: str = "webhook"  # "webhook" or "simulated"

    # App URLs
    APP_BASE_URL: str
    FRONTEND_URL: str

    # Webhook Security
    WEBHOOK_USERNAME: str
    WEBHOOK_PASSWORD: str

    # Worker Settings
    WORKER_POLL_INTERVAL_SECONDS: int = 5  # Check for pending emails every 5 seconds
    MAX_RETRY_ATTEMPTS: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
