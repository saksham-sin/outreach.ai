"""Resend email provider implementation."""

import httpx
from typing import Optional
import logging

from app.core.config import get_settings
from app.core.constants import EmailType
from app.infrastructure.email_provider import (
    EmailProvider,
    EmailMetadata,
    EmailResult,
    EmailProviderError,
)

logger = logging.getLogger(__name__)
settings = get_settings()

RESEND_API_BASE_URL = "https://api.resend.com"


class ResendProvider(EmailProvider):
    """Email provider implementation using Resend API."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        # Dual sender configuration
        self.auth_from_email = settings.EMAIL_AUTH_FROM_ADDRESS or settings.EMAIL_FROM_ADDRESS
        self.auth_from_name = settings.EMAIL_AUTH_FROM_NAME or settings.EMAIL_FROM_NAME
        self.outreach_from_email = settings.EMAIL_OUTREACH_FROM_ADDRESS or settings.EMAIL_FROM_ADDRESS
        self.outreach_from_name = settings.EMAIL_OUTREACH_FROM_NAME or settings.EMAIL_FROM_NAME
        self.outreach_reply_to = settings.EMAIL_OUTREACH_REPLY_TO or settings.EMAIL_OUTREACH_FROM_ADDRESS
        # Legacy fallback
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME
        self.inbound_address = (
            settings.RESEND_INBOUND_ADDRESS
            or settings.EMAIL_OUTREACH_REPLY_TO
            or settings.EMAIL_OUTREACH_FROM_ADDRESS
            or None
        )
        self.from_domain = settings.RESEND_FROM_DOMAIN
    
    def _get_sender_config(self, email_type: EmailType) -> tuple[str, str]:
        """
        Get sender email and name based on email type.
        
        Args:
            email_type: Type of email (AUTH or OUTREACH)
            
        Returns:
            Tuple of (from_email, from_name)
        """
        if email_type == EmailType.AUTH:
            return self.auth_from_email, self.auth_from_name
        else:  # EmailType.OUTREACH
            return self.outreach_from_email, self.outreach_from_name

    def _get_headers(self) -> dict:
        """Get headers for Resend API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get_reply_to_address(self, lead_id) -> Optional[str]:
        """
        Generate a reply-to address for reply detection.
        Format: reply+{lead_id}@domain.com
        """
        if not self.inbound_address or "@" not in self.inbound_address:
            return None
        local_part, domain = self.inbound_address.split("@")
        return f"{local_part}+{lead_id}@{domain}"

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
        Send a campaign email via Resend.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML body content
            text_body: Optional plain text body
            metadata: Campaign/lead tracking metadata
            track_opens: Whether to track email opens
            track_links: Whether to track link clicks
            from_email: Optional custom from email (overrides email_type routing)
            email_type: Type of email (AUTH or OUTREACH) for sender routing
            
        Returns:
            EmailResult with success status and message ID
        """
        # Get sender configuration based on email type
        sender_email, sender_name = self._get_sender_config(email_type)
        
        # Use custom from_email if provided, otherwise use type-based sender
        email_address = from_email or sender_email
        
        payload = {
            "from": f"{sender_name} <{email_address}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }

        # Add text body if provided
        if text_body:
            payload["text"] = text_body

        # Configure reply-to based on email type
        if email_type == EmailType.OUTREACH:
            # For OUTREACH emails, use configured reply-to or add lead-specific reply tracking
            if metadata and metadata.lead_id:
                # Use lead-specific reply-to for reply detection
                reply_to = self._get_reply_to_address(metadata.lead_id)
                if reply_to:
                    payload["reply_to"] = reply_to
            elif self.outreach_reply_to:
                # Use configured outreach reply-to
                payload["reply_to"] = self.outreach_reply_to
        # For AUTH emails, no reply-to (no replies expected)

        # Add headers for metadata tracking (Resend supports custom headers)
        headers = {}
        if metadata:
            if metadata.campaign_id:
                headers["X-Campaign-Id"] = str(metadata.campaign_id)
            if metadata.lead_id:
                headers["X-Lead-Id"] = str(metadata.lead_id)
            if metadata.step_number:
                headers["X-Step-Number"] = str(metadata.step_number)
        
        if headers:
            payload["headers"] = headers

        # Add tags for tracking
        tags = []
        if metadata:
            if metadata.campaign_id:
                tags.append({"name": "campaign_id", "value": str(metadata.campaign_id)})
            if metadata.lead_id:
                tags.append({"name": "lead_id", "value": str(metadata.lead_id)})
            if metadata.step_number:
                tags.append({"name": "step_number", "value": str(metadata.step_number)})
        
        if tags:
            payload["tags"] = tags

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{RESEND_API_BASE_URL}/emails",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0,
                )
                
                result = response.json()
                
                if response.status_code not in (200, 201):
                    error_message = result.get("message", "Unknown error")
                    logger.error(f"Resend API error: {error_message}")
                    return EmailResult(
                        success=False,
                        error=error_message,
                    )
                
                message_id = result.get("id")
                logger.info(
                    f"Email sent successfully via Resend to {to_email}, "
                    f"MessageID: {message_id}"
                )
                return EmailResult(
                    success=True,
                    message_id=message_id,
                )
                
            except httpx.HTTPError as e:
                error_msg = f"HTTP error: {str(e)}"
                logger.error(f"Resend HTTP error sending email: {error_msg}")
                return EmailResult(
                    success=False,
                    error=error_msg,
                )

    async def send_transactional_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        email_type: EmailType = EmailType.AUTH,
    ) -> EmailResult:
        """
        Send a simple transactional email (e.g., magic links) via Resend.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            email_type: Type of email (AUTH or OUTREACH) for sender routing
            
        Returns:
            EmailResult with success status
        """
        # Get sender configuration based on email type
        sender_email, sender_name = self._get_sender_config(email_type)
        
        payload = {
            "from": f"{sender_name} <{sender_email}>",
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
        
        # For OUTREACH transactional emails, add reply-to
        # For AUTH emails (magic links), no reply-to needed
        if email_type == EmailType.OUTREACH and self.outreach_reply_to:
            payload["reply_to"] = self.outreach_reply_to

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{RESEND_API_BASE_URL}/emails",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0,
                )
                
                result = response.json()
                
                if response.status_code not in (200, 201):
                    error_message = result.get("message", "Unknown error")
                    logger.error(f"Resend API error for transactional email: {error_message}")
                    return EmailResult(
                        success=False,
                        error=error_message,
                    )
                
                logger.info(f"Transactional email sent via Resend to {to_email}")
                return EmailResult(
                    success=True,
                    message_id=result.get("id"),
                )
                
            except httpx.HTTPError as e:
                error_msg = f"HTTP error: {str(e)}"
                logger.error(f"Resend HTTP error sending transactional email: {error_msg}")
                return EmailResult(
                    success=False,
                    error=error_msg,
                )


# Singleton instance
_resend_provider: Optional[ResendProvider] = None


def get_resend_provider() -> ResendProvider:
    """Get or create Resend provider instance."""
    global _resend_provider
    if _resend_provider is None:
        _resend_provider = ResendProvider()
    return _resend_provider
