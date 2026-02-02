"""Postmark email provider implementation."""

import httpx
from typing import Optional
from uuid import UUID
import logging

from app.core.config import get_settings
from app.core.constants import POSTMARK_API_BASE_URL, POSTMARK_SEND_ENDPOINT
from app.infrastructure.email_provider import (
    EmailProvider,
    EmailMetadata,
    EmailResult,
    EmailProviderError,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class PostmarkError(Exception):
    """Custom exception for Postmark API errors (kept for backwards compatibility)."""
    
    def __init__(self, message: str, error_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class PostmarkProvider(EmailProvider):
    """Email provider implementation using Postmark API."""

    def __init__(self):
        self.base_url = POSTMARK_API_BASE_URL
        self.server_token = settings.POSTMARK_SERVER_TOKEN
        self.from_email = getattr(settings, 'EMAIL_FROM_ADDRESS', settings.FROM_EMAIL)
        self.from_name = getattr(settings, 'EMAIL_FROM_NAME', settings.FROM_NAME)
        self.inbound_address = settings.POSTMARK_INBOUND_ADDRESS

    def _get_headers(self) -> dict:
        """Get headers for Postmark API requests."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.server_token,
        }

    def _get_reply_to_address(self, lead_id: UUID) -> Optional[str]:
        """
        Generate a reply-to address with MailboxHash for reply detection.
        Returns None if inbound address is not configured.
        Format: reply+{lead_id}@domain.com
        """
        if not self.inbound_address or "@" not in self.inbound_address:
            # Inbound address not configured - skip reply-to setup
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
    ) -> EmailResult:
        """
        Send a campaign email via Postmark.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML body content
            text_body: Optional plain text body
            metadata: Campaign/lead tracking metadata
            track_opens: Whether to track email opens
            track_links: Whether to track link clicks
            from_email: Optional custom from email (defaults to self.from_email)
            
        Returns:
            EmailResult with success status and message ID
        """
        # Use custom from_email if provided, otherwise use configured default
        email_address = from_email or self.from_email
        
        payload = {
            "From": f"{self.from_name} <{email_address}>",
            "To": to_email,
            "Subject": subject,
            "HtmlBody": html_body,
            "TrackOpens": track_opens,
            "TrackLinks": "HtmlAndText" if track_links else "None",
            "MessageStream": "outbound",
        }

        # Add text body if provided
        if text_body:
            payload["TextBody"] = text_body

        # Add reply-to with MailboxHash for reply detection (if configured)
        if metadata and metadata.lead_id:
            reply_to = self._get_reply_to_address(metadata.lead_id)
            if reply_to:
                payload["ReplyTo"] = reply_to

        # Add metadata for tracking
        postmark_metadata = {}
        if metadata:
            if metadata.campaign_id:
                postmark_metadata["campaign_id"] = str(metadata.campaign_id)
            if metadata.lead_id:
                postmark_metadata["lead_id"] = str(metadata.lead_id)
            if metadata.step_number:
                postmark_metadata["step_number"] = str(metadata.step_number)
        
        if postmark_metadata:
            payload["Metadata"] = postmark_metadata

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}{POSTMARK_SEND_ENDPOINT}",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0,
                )
                
                result = response.json()
                
                if response.status_code != 200:
                    error_code = result.get("ErrorCode", 0)
                    error_message = result.get("Message", "Unknown error")
                    logger.error(
                        f"Postmark API error: {error_message} (code: {error_code})"
                    )
                    return EmailResult(
                        success=False,
                        error=f"{error_message} (code: {error_code})",
                    )
                
                message_id = result.get("MessageID")
                logger.info(
                    f"Email sent successfully via Postmark to {to_email}, "
                    f"MessageID: {message_id}"
                )
                return EmailResult(
                    success=True,
                    message_id=message_id,
                )
                
            except httpx.HTTPError as e:
                error_msg = f"HTTP error: {str(e)}"
                logger.error(f"HTTP error sending email: {error_msg}")
                return EmailResult(
                    success=False,
                    error=error_msg,
                )

    async def send_transactional_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> EmailResult:
        """
        Send a simple transactional email (e.g., magic links) via Postmark.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            
        Returns:
            EmailResult with success status
        """
        payload = {
            "From": f"{self.from_name} <{self.from_email}>",
            "To": to_email,
            "Subject": subject,
            "TextBody": body,
            "MessageStream": "outbound",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}{POSTMARK_SEND_ENDPOINT}",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0,
                )
                
                result = response.json()
                
                if response.status_code != 200:
                    error_code = result.get("ErrorCode", 0)
                    error_message = result.get("Message", "Unknown error")
                    return EmailResult(
                        success=False,
                        error=f"{error_message} (code: {error_code})",
                    )
                
                logger.info(f"Transactional email sent via Postmark to {to_email}")
                return EmailResult(
                    success=True,
                    message_id=result.get("MessageID"),
                )
                
            except httpx.HTTPError as e:
                error_msg = f"HTTP error: {str(e)}"
                logger.error(f"HTTP error sending magic link: {error_msg}")
                return EmailResult(
                    success=False,
                    error=error_msg,
                )


# Singleton instance
_postmark_provider: Optional[PostmarkProvider] = None


def get_postmark_provider() -> PostmarkProvider:
    """Get or create Postmark provider instance."""
    global _postmark_provider
    if _postmark_provider is None:
        _postmark_provider = PostmarkProvider()
    return _postmark_provider


# ============================================================================
# LEGACY COMPATIBILITY LAYER
# Keep old PostmarkClient class for backwards compatibility during migration
# ============================================================================

class PostmarkClient:
    """
    Legacy Postmark client - DEPRECATED.
    Use get_email_provider() from email_factory instead.
    """

    def __init__(self):
        self._provider = PostmarkProvider()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        campaign_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        step_number: Optional[int] = None,
        track_opens: bool = True,
        track_links: str = "HtmlAndText",
    ) -> dict:
        """Legacy send_email method for backwards compatibility."""
        metadata = EmailMetadata(
            campaign_id=campaign_id,
            lead_id=lead_id,
            step_number=step_number,
        )
        result = await self._provider.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            metadata=metadata,
            track_opens=track_opens,
            track_links=track_links != "None",
        )
        
        if not result.success:
            raise PostmarkError(result.error or "Unknown error")
        
        return {"MessageID": result.message_id}

    async def send_magic_link_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> dict:
        """Legacy send_magic_link_email method for backwards compatibility."""
        result = await self._provider.send_transactional_email(
            to_email=to_email,
            subject=subject,
            body=body,
        )
        
        if not result.success:
            raise PostmarkError(result.error or "Unknown error")
        
        return {"MessageID": result.message_id}


# Legacy singleton
_postmark_client: Optional[PostmarkClient] = None


def get_postmark_client() -> PostmarkClient:
    """
    Get or create legacy Postmark client instance.
    DEPRECATED: Use get_email_provider() from email_factory instead.
    """
    global _postmark_client
    if _postmark_client is None:
        _postmark_client = PostmarkClient()
    return _postmark_client
