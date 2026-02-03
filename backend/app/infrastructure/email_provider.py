"""Abstract email provider interface for email delivery abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.core.constants import EmailType


@dataclass
class EmailMetadata:
    """Metadata for tracking email deliveries."""
    campaign_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    step_number: Optional[int] = None


@dataclass
class EmailResult:
    """Result from sending an email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        metadata: Optional[EmailMetadata] = None,
        track_opens: bool = True,
        track_links: bool = True,
        from_email: Optional[str] = None,
        email_type: EmailType = EmailType.OUTREACH,
    ) -> EmailResult:
        """
        Send a campaign email with tracking and reply detection.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML body content
            text_body: Optional plain text body
            metadata: Campaign/lead tracking metadata
            track_opens: Whether to track email opens
            track_links: Whether to track link clicks
            from_email: Optional custom from email (defaults to sender based on email_type)
            email_type: Type of email (AUTH or OUTREACH) for sender routing
            
        Returns:
            EmailResult with success status and message ID
        """
        pass

    @abstractmethod
    async def send_transactional_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        email_type: EmailType = EmailType.AUTH,
    ) -> EmailResult:
        """
        Send a simple transactional email (e.g., magic links).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            email_type: Type of email (AUTH or OUTREACH) for sender routing
            
        Returns:
            EmailResult with success status
        """
        pass


class EmailProviderError(Exception):
    """Custom exception for email provider errors."""
    
    def __init__(self, message: str, error_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
