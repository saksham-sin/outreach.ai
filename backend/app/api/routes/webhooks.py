"""Webhook endpoints for Resend inbound events."""

import logging
import re
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from svix.webhooks import Webhook, WebhookVerificationError

from app.api.dependencies import SessionDep
from app.core.config import get_settings
from app.services.lead_service import LeadService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks/resend", tags=["Webhooks"])

FIELDS_TO_SCAN = ("to", "reply_to", "replyTo", "from", "cc", "bcc")
HEADER_FIELDS_TO_SCAN = {"reply-to", "to", "from"}


def _add_candidate_value(candidates: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, list):
        for item in value:
            _add_candidate_value(candidates, item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _add_candidate_value(candidates, item)
        return
    candidates.append(str(value))


def _add_candidate_fields(candidates: list[str], container: Any) -> None:
    if not isinstance(container, dict):
        return
    for field in FIELDS_TO_SCAN:
        _add_candidate_value(candidates, container.get(field))


def _add_candidate_headers(candidates: list[str], container: Any) -> None:
    if not isinstance(container, list):
        return
    for header in container:
        if not isinstance(header, dict):
            continue
        name = str(header.get("name", "")).lower()
        if name in HEADER_FIELDS_TO_SCAN:
            _add_candidate_value(candidates, header.get("value"))


def _extract_candidate_strings(payload: dict[str, Any]) -> list[str]:
    """Extract all candidate strings from webhook payload that might contain lead ID."""
    candidates: list[str] = []

    _add_candidate_fields(candidates, payload)
    _add_candidate_fields(candidates, payload.get("data"))
    _add_candidate_headers(candidates, payload.get("headers"))

    return candidates


def _extract_lead_id(payload: dict[str, Any]) -> UUID | None:
    """Extract lead ID from webhook payload.
    
    The lead ID is typically encoded in the recipient email address:
    hello+<lead-id>@example.com
    """
    candidates = _extract_candidate_strings(payload)
    uuid_pattern = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

    logger.debug(f"Searching for lead ID in {len(candidates)} candidate strings")
    
    for value in candidates:
        logger.debug(f"Checking candidate: {value}")
        match = uuid_pattern.search(value)
        if not match:
            continue
        try:
            found_id = UUID(match.group(0))
            logger.info(f"Found lead ID: {found_id}")
            return found_id
        except ValueError:
            continue
    
    logger.error(f"No valid UUID found in candidates: {candidates}")
    return None


def _verify_resend_signature(headers: dict[str, str], body: bytes) -> None:
    """Verify Resend webhook signature using Svix library.
    
    Resend uses Svix-style webhook signing with headers:
    - svix-id: Message ID
    - svix-timestamp: Timestamp of message
    - svix-signature: Signature in format "v1,signature_value"
    """
    secret = settings.RESEND_WEBHOOK_SECRET
    if not secret:
        logger.warning("RESEND_WEBHOOK_SECRET not set - webhook signature verification disabled")
        return

    try:
        # Use Svix library to verify the webhook
        wh = Webhook(secret)
        
        # Convert body to string if it's bytes
        payload_str = body.decode('utf-8') if isinstance(body, bytes) else body
        
        # Verify the webhook - this will raise WebhookVerificationError if invalid
        wh.verify(payload_str, headers)
        logger.debug("Webhook signature verified successfully")
        
    except WebhookVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        logger.debug(f"Headers: {dict(headers)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")


@router.post("/inbound", summary="Handle Resend inbound reply")
async def resend_inbound(
    request: Request,
    session: SessionDep,
) -> dict[str, str | bool]:
    reply_mode = (settings.REPLY_MODE or "SIMULATED").upper()
    if reply_mode != "RESEND-WEBHOOK":
        logger.info("Reply mode is not RESEND-WEBHOOK; inbound webhook ignored")
        return {
            "success": False,
            "message": "Reply mode is not RESEND-WEBHOOK; inbound ignored",
        }

    body = await request.body()
    logger.info("Received webhook request")
    _verify_resend_signature(dict(request.headers), body)

    payload = json.loads(body.decode("utf-8") or "{}")
    lead_id = _extract_lead_id(payload)
    if not lead_id:
        logger.warning("Resend inbound webhook received but no lead id found")
        return {
            "success": False,
            "message": "No lead id found in inbound payload",
        }

    service = LeadService(session)
    lead = await service.mark_lead_replied(lead_id)
    if not lead:
        return {
            "success": False,
            "message": "Lead not found",
        }

    await session.commit()
    logger.info(f"Inbound reply detected for lead {lead_id}")

    return {
        "success": True,
        "message": f"Lead {lead_id} marked as replied",
    }
