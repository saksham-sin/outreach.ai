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
    RESEND_FROM_DOMAIN: str = ""  # Custom domain for sending emails
    
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


def get_user_email(first_name: str) -> str:
    """
    Generate a user-specific email address using their first name.
    
    Args:
        first_name: User's first name
        
    Returns:
        User-specific email address in the format: {first_name}@{domain}
        Falls back to default if first_name is empty or invalid
    """
    settings = get_settings()
    
    if not first_name or not first_name.strip():
        # Return fallback email if no first_name provided
        return settings.EMAIL_FROM_ADDRESS
    
    # Sanitize first_name: lowercase, remove non-alphanumeric chars except hyphens/underscores
    clean_name = first_name.lower().strip()
    clean_name = "".join(c if c.isalnum() or c in "-_" else "" for c in clean_name)
    
    if not clean_name:
        # Return fallback if sanitization resulted in empty string
        return settings.EMAIL_FROM_ADDRESS
    
    # Extract domain from configured email address
    if "@" not in settings.EMAIL_FROM_ADDRESS:
        return settings.EMAIL_FROM_ADDRESS
    
    domain = settings.EMAIL_FROM_ADDRESS.split("@")[1]
    
    # Return user-specific email
    return f"{clean_name}@{domain}"
