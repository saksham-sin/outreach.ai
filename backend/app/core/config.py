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
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini"

    # Email Sender Configuration (Dual Sender Identity)
    # AUTH emails: Magic links, transactional (no-reply)
    EMAIL_AUTH_FROM_ADDRESS: str = ""  # e.g., no-reply@outreachai-demo.online
    EMAIL_AUTH_FROM_NAME: str = "Outreach AI"
    
    # OUTREACH emails: Campaign and follow-ups (replies expected)
    EMAIL_OUTREACH_FROM_ADDRESS: str = ""  # e.g., hello@outreachai-demo.online
    EMAIL_OUTREACH_FROM_NAME: str = "Outreach AI"
    EMAIL_OUTREACH_REPLY_TO: str = ""  # e.g., hello@outreachai-demo.online (same as from)
    
    # Legacy unified email settings (deprecated - use specific AUTH/OUTREACH settings above)
    EMAIL_FROM_ADDRESS: str = ""  # Fallback for backwards compatibility
    EMAIL_FROM_NAME: str = "Outreach AI"  # Fallback for backwards compatibility
    
    # Resend Email Provider (sole production provider)
    RESEND_API_KEY: str = ""
    RESEND_FROM_DOMAIN: str = ""  # Custom domain for sending emails

    # App URLs
    APP_BASE_URL: str
    FRONTEND_URL: str

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
