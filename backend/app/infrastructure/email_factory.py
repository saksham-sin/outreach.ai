"""Factory for creating email provider instances based on configuration."""

from typing import Optional
import logging

from app.core.config import get_settings
from app.infrastructure.email_provider import EmailProvider

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton provider instance
_email_provider: Optional[EmailProvider] = None


def get_email_provider() -> EmailProvider:
    """
    Get the configured email provider instance.
    
    Returns provider based on EMAIL_PROVIDER env var:
    - "resend": Returns ResendProvider
    - "postmark": Returns PostmarkProvider (default)
    
    Returns:
        EmailProvider instance
    """
    global _email_provider
    
    if _email_provider is not None:
        return _email_provider
    
    provider_name = getattr(settings, 'EMAIL_PROVIDER', 'postmark').lower()
    
    if provider_name == "resend":
        from app.infrastructure.resend_provider import ResendProvider
        _email_provider = ResendProvider()
        logger.info("Using Resend email provider")
    else:
        # Default to Postmark
        from app.infrastructure.postmark_provider import PostmarkProvider
        _email_provider = PostmarkProvider()
        logger.info("Using Postmark email provider")
    
    return _email_provider


def reset_email_provider() -> None:
    """Reset the cached provider instance (useful for testing)."""
    global _email_provider
    _email_provider = None
