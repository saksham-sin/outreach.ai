"""Factory for creating email provider instances.

Resend is the sole production provider.
"""

from typing import Optional
import logging

from app.infrastructure.email_provider import EmailProvider
from app.infrastructure.resend_provider import ResendProvider

logger = logging.getLogger(__name__)

# Singleton provider instance
_email_provider: Optional[EmailProvider] = None


def get_email_provider() -> EmailProvider:
    """
    Get the email provider instance (Resend).
    
    Returns:
        ResendProvider instance
    """
    global _email_provider
    
    if _email_provider is not None:
        return _email_provider
    
    _email_provider = ResendProvider()
    logger.info("Using Resend email provider")
    
    return _email_provider


def reset_email_provider() -> None:
    """Reset the cached provider instance (useful for testing)."""
    global _email_provider
    _email_provider = None
