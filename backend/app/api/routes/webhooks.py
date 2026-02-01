"""Webhook API routes for Postmark inbound emails."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
import logging

from app.api.dependencies import SessionDep, WebhookAuth
from app.services.lead_service import LeadService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


class InboundEmailPayload(BaseModel):
    """Postmark inbound email webhook payload (relevant fields)."""
    From: str
    To: str
    Subject: str
    MessageID: str
    MailboxHash: Optional[str] = None
    TextBody: Optional[str] = None
    StrippedTextReply: Optional[str] = None


class WebhookResponse(BaseModel):
    """Standard webhook response."""
    status: str
    message: str


@router.post(
    "/postmark/inbound",
    response_model=WebhookResponse,
    summary="Postmark inbound webhook",
    description="Handle inbound email replies from Postmark.",
)
async def handle_inbound_email(
    request: Request,
    session: SessionDep,
    _auth: WebhookAuth,
) -> WebhookResponse:
    """
    Handle inbound email webhook from Postmark.
    
    Extracts lead_id from MailboxHash and marks the lead as replied.
    Uses HTTP Basic Auth for security.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    
    # Extract MailboxHash (contains lead_id)
    mailbox_hash = payload.get("MailboxHash")
    from_email = payload.get("From", "unknown")
    subject = payload.get("Subject", "")
    
    logger.info(
        f"Inbound email received from {from_email}, "
        f"MailboxHash: {mailbox_hash}, Subject: {subject}"
    )
    
    if not mailbox_hash:
        logger.warning("Inbound email without MailboxHash - ignoring")
        return WebhookResponse(
            status="ignored",
            message="No MailboxHash found",
        )
    
    # Parse lead_id from MailboxHash
    try:
        lead_id = UUID(mailbox_hash)
    except ValueError:
        logger.warning(f"Invalid lead_id in MailboxHash: {mailbox_hash}")
        return WebhookResponse(
            status="ignored",
            message="Invalid MailboxHash format",
        )
    
    # Mark lead as replied
    lead_service = LeadService(session)
    lead = await lead_service.mark_lead_replied(lead_id)
    
    if not lead:
        logger.warning(f"Lead not found for MailboxHash: {mailbox_hash}")
        return WebhookResponse(
            status="ignored",
            message="Lead not found",
        )
    
    logger.info(f"Lead {lead_id} marked as replied")
    
    return WebhookResponse(
        status="success",
        message=f"Lead {lead_id} marked as replied",
    )


@router.post(
    "/postmark/bounce",
    response_model=WebhookResponse,
    summary="Postmark bounce webhook",
    description="Handle bounce notifications from Postmark.",
)
async def handle_bounce(
    request: Request,
    session: SessionDep,
    _auth: WebhookAuth,
) -> WebhookResponse:
    """
    Handle bounce webhook from Postmark.
    
    Logs bounce information for monitoring.
    The email job retry logic handles failures automatically.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse bounce payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    
    bounce_type = payload.get("Type", "unknown")
    email = payload.get("Email", "unknown")
    description = payload.get("Description", "")
    metadata = payload.get("Metadata", {})
    
    logger.warning(
        f"Bounce received: {bounce_type} for {email}. "
        f"Description: {description}. Metadata: {metadata}"
    )
    
    return WebhookResponse(
        status="received",
        message=f"Bounce logged for {email}",
    )


@router.post(
    "/postmark/delivery",
    response_model=WebhookResponse,
    summary="Postmark delivery webhook",
    description="Handle delivery notifications from Postmark.",
)
async def handle_delivery(
    request: Request,
    _auth: WebhookAuth,
) -> WebhookResponse:
    """
    Handle delivery webhook from Postmark.
    
    Logs successful deliveries for monitoring.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse delivery payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    
    email = payload.get("Recipient", "unknown")
    metadata = payload.get("Metadata", {})
    
    logger.info(f"Delivery confirmed for {email}. Metadata: {metadata}")
    
    return WebhookResponse(
        status="received",
        message=f"Delivery logged for {email}",
    )
