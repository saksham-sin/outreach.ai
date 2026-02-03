"""Webhook endpoints for Resend inbound events."""

import logging
import re
import secrets
import hmac
import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies import SessionDep
from app.core.config import get_settings
from app.services.lead_service import LeadService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks/resend", tags=["Webhooks"])


def _extract_candidate_strings(payload: dict[str, Any]) -> list[str]:
    candidates: list[str] = []

    def add_value(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, list):
            for item in value:
                add_value(item)
            return
        if isinstance(value, dict):
            for item in value.values():
                add_value(item)
            return
        candidates.append(str(value))

    add_value(payload.get("to"))
    add_value(payload.get("reply_to"))
    add_value(payload.get("replyTo"))
    add_value(payload.get("from"))
    add_value(payload.get("cc"))
    add_value(payload.get("bcc"))

    headers = payload.get("headers")
    if isinstance(headers, list):
        for header in headers:
            if not isinstance(header, dict):
                continue
            name = str(header.get("name", "")).lower()
            if name in {"reply-to", "to", "from"}:
                add_value(header.get("value"))

    return candidates


def _extract_lead_id(payload: dict[str, Any]) -> UUID | None:
    candidates = _extract_candidate_strings(payload)
    uuid_pattern = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

    for value in candidates:
        match = uuid_pattern.search(value)
        if not match:
            continue
        try:
            return UUID(match.group(0))
        except ValueError:
            continue
    return None


def _verify_resend_signature(headers: dict[str, str], body: bytes) -> None:
    secret = settings.RESEND_WEBHOOK_SECRET
    if not secret:
        return

    signature_header = headers.get("resend-signature") or headers.get("Resend-Signature")
    timestamp_header = headers.get("resend-timestamp") or headers.get("Resend-Timestamp")

    # Support svix-style headers if provided
    if not signature_header:
        signature_header = headers.get("svix-signature") or headers.get("Svix-Signature")
    if not timestamp_header:
        timestamp_header = headers.get("svix-timestamp") or headers.get("Svix-Timestamp")

    if signature_header and timestamp_header:
        timestamp = timestamp_header.strip()
        signatures = [sig.strip() for sig in signature_header.split(",") if sig.strip()]
        digest = hmac.new(
            secret.encode("utf-8"),
            msg=f"{timestamp}.{body.decode('utf-8')}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if any(secrets.compare_digest(digest, sig.split("=")[-1]) for sig in signatures):
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Support resend-signature format: t=...,v1=...
    if signature_header:
        parts = {}
        for piece in signature_header.split(","):
            if "=" not in piece:
                continue
            key, value = piece.strip().split("=", 1)
            parts[key] = value
        timestamp = parts.get("t")
        v1 = parts.get("v1")
        if not timestamp or not v1:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
        digest = hmac.new(
            secret.encode("utf-8"),
            msg=f"{timestamp}.{body.decode('utf-8')}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not secrets.compare_digest(digest, v1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
        return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")


@router.post("/inbound", summary="Handle Resend inbound reply")
async def resend_inbound(
    request: Request,
    session: SessionDep,
) -> dict[str, str | bool]:
    reply_mode = (settings.REPLY_MODE or "SIMULATED").upper()
    if reply_mode != "RESEND-WEBHOOK":
        return {
            "success": False,
            "message": "Reply mode is not RESEND-WEBHOOK; inbound ignored",
        }

    body = await request.body()
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
