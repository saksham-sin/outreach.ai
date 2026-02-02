"""Lead API routes."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel

from app.api.dependencies import SessionDep, CurrentUser
from app.services.lead_service import LeadService, LeadError
from app.models.lead import LeadCreate, LeadRead, LeadImportResult
from app.domain.enums import LeadStatus
from app.core.config import get_settings

router = APIRouter(prefix="/campaigns/{campaign_id}/leads", tags=["Leads"])
settings = get_settings()


class LeadListResponse(BaseModel):
    """Response containing list of leads."""
    leads: list[LeadRead]
    total: int


class CopyLeadsRequest(BaseModel):
    """Request to copy leads from another campaign."""
    source_campaign_id: UUID


class CopyLeadsResponse(BaseModel):
    """Response after copying leads."""
    copied: int


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create lead",
    description="Create a single lead for a campaign.",
)
async def create_lead(
    campaign_id: UUID,
    data: LeadCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> LeadRead:
    """
    Create a single lead.
    
    The campaign must be in DRAFT status.
    """
    service = LeadService(session)
    
    try:
        lead = await service.create_lead(campaign_id, current_user.id, data)
        
        return LeadRead(
            id=lead.id,
            campaign_id=lead.campaign_id,
            email=lead.email,
            first_name=lead.first_name,
            company=lead.company,
            status=lead.status,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )
    except LeadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=LeadListResponse,
    summary="List leads",
    description="List leads for a campaign.",
)
async def list_leads(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    status_filter: Optional[LeadStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> LeadListResponse:
    """
    List leads for a campaign.
    
    Supports filtering by status and pagination.
    """
    from sqlalchemy import func, select
    from app.models.campaign import Campaign
    from app.models.lead import Lead
    
    service = LeadService(session)
    
    try:
        # Verify campaign ownership
        campaign_result = await session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
        )
        if not campaign_result.scalar_one_or_none():
            raise LeadError("Campaign not found")
        
        # Get total count
        count_query = select(func.count(Lead.id)).where(Lead.campaign_id == campaign_id)
        if status_filter:
            count_query = count_query.where(Lead.status == status_filter)
        
        total_result = await session.execute(count_query)
        total_count = total_result.scalar() or 0
        
        # Get paginated leads
        leads = await service.list_leads(
            campaign_id, current_user.id, status_filter, skip, limit
        )
        
        return LeadListResponse(
            leads=[
                LeadRead(
                    id=l.id,
                    campaign_id=l.campaign_id,
                    email=l.email,
                    first_name=l.first_name,
                    company=l.company,
                    status=l.status,
                    created_at=l.created_at,
                    updated_at=l.updated_at,
                )
                for l in leads
            ],
            total=total_count,
        )
    except LeadError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/import",
    response_model=LeadImportResult,
    summary="Import leads from CSV",
    description="Import leads from a CSV file.",
)
async def import_leads(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> LeadImportResult:
    """
    Import leads from a CSV file.
    
    The CSV must have an 'email' column. Optional columns:
    'first_name', 'company'.
    
    The campaign must be in DRAFT status.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )
    
    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file encoding. Please use UTF-8.",
        )
    
    service = LeadService(session)
    
    try:
        result = await service.import_leads_csv(
            campaign_id, current_user.id, csv_content
        )
        return result
    except LeadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/copy",
    response_model=CopyLeadsResponse,
    summary="Copy leads from another campaign",
    description="Copy leads from another campaign.",
)
async def copy_leads(
    campaign_id: UUID,
    request: CopyLeadsRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> CopyLeadsResponse:
    """
    Copy leads from another campaign.
    
    Duplicates are skipped. The target campaign must be in DRAFT status.
    """
    service = LeadService(session)
    
    try:
        copied = await service.copy_leads_from_campaign(
            request.source_campaign_id, campaign_id, current_user.id
        )
        return CopyLeadsResponse(copied=copied)
    except LeadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{lead_id}",
    response_model=LeadRead,
    summary="Get lead",
    description="Get a single lead by ID.",
)
async def get_lead(
    campaign_id: UUID,
    lead_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> LeadRead:
    """Get a single lead by ID."""
    service = LeadService(session)
    lead = await service.get_lead(lead_id, current_user.id)
    
    if not lead or lead.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    return LeadRead(
        id=lead.id,
        campaign_id=lead.campaign_id,
        email=lead.email,
        first_name=lead.first_name,
        company=lead.company,
        status=lead.status,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


class MarkRepliedResponse(BaseModel):
    """Response after marking a lead as replied."""
    success: bool
    message: str


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a lead",
    description="Delete a lead from a campaign. Only works for draft campaigns.",
)
async def delete_lead(
    campaign_id: UUID,
    lead_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """
    Delete a lead from a campaign.
    
    Only works when campaign is in draft status.
    """
    service = LeadService(session)
    success = await service.delete_lead(lead_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or cannot be deleted",
        )


@router.post(
    "/{lead_id}/mark-replied",
    response_model=MarkRepliedResponse,
    summary="Mark lead as replied (simulated)",
    description="Manually mark a lead as having replied. Only works when REPLY_MODE=simulated.",
)
async def mark_lead_replied(
    campaign_id: UUID,
    lead_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> MarkRepliedResponse:
    """
    Mark a lead as having replied (for simulated reply mode).
    
    This endpoint allows manual marking of leads as replied when
    webhook-based reply detection is not available (REPLY_MODE=simulated).
    
    Only works when REPLY_MODE is set to 'simulated'.
    Also cancels all pending follow-up emails for this lead.
    """
    # Check if simulated reply mode is enabled
    reply_mode = getattr(settings, 'REPLY_MODE', 'webhook')
    if reply_mode != 'simulated':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual reply marking is only available in simulated mode. Set REPLY_MODE=simulated to enable.",
        )
    
    service = LeadService(session)
    lead = await service.get_lead(lead_id, current_user.id)
    
    if not lead or lead.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    # Check if lead is in a state that can receive a reply
    if lead.status == LeadStatus.REPLIED:
        return MarkRepliedResponse(
            success=True,
            message="Lead already marked as replied",
        )
    
    if lead.status not in (LeadStatus.CONTACTED, LeadStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark lead as replied. Current status: {lead.status.value}",
        )
    
    # Use the service method which also cancels pending jobs
    await service.mark_lead_replied(lead_id)
    await session.commit()
    
    return MarkRepliedResponse(
        success=True,
        message=f"Lead {lead.email} marked as replied",
    )

class EmailSendEvent(BaseModel):
    """Single email send event in the timeline."""
    step_number: int
    status: str  # 'sent', 'pending', 'failed', 'skipped'
    scheduled_at: datetime
    sent_at: Optional[datetime]
    subject: str
    attempts: int
    last_error: Optional[str]


class EmailHistoryResponse(BaseModel):
    """Response containing email send history for a lead."""
    lead_id: UUID
    email: str
    events: list[EmailSendEvent]


@router.get(
    "/{lead_id}/email-history",
    response_model=EmailHistoryResponse,
    summary="Get email send history",
    description="Get the email send history and timeline for a specific lead.",
)
async def get_lead_email_history(
    campaign_id: UUID,
    lead_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmailHistoryResponse:
    """
    Get email send history for a lead.
    
    Returns a timeline of all email send events for the lead, including
    sent timestamps, status, and any error messages.
    """
    from sqlalchemy import select
    from app.models.campaign import Campaign
    from app.models.lead import Lead
    from app.models.email_job import EmailJob
    
    # Verify campaign belongs to user and lead belongs to campaign
    result = await session.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    
    # Get the lead
    result = await session.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.campaign_id == campaign_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    
    # Get all email jobs for this lead, ordered by step and creation date
    result = await session.execute(
        select(EmailJob)
        .where(EmailJob.lead_id == lead_id)
        .order_by(EmailJob.step_number, EmailJob.created_at)
    )
    jobs = list(result.scalars().all())
    
    # Get templates to fetch subject lines
    from app.models.email_template import EmailTemplate
    result = await session.execute(
        select(EmailTemplate).where(EmailTemplate.campaign_id == campaign_id)
    )
    templates = {t.step_number: t for t in result.scalars().all()}
    
    # Convert jobs to events
    events = []
    for job in jobs:
        template = templates.get(job.step_number)
        events.append(EmailSendEvent(
            step_number=job.step_number,
            status=job.status.value,
            scheduled_at=job.scheduled_at,
            sent_at=job.sent_at,
            subject=template.subject if template else f"Step {job.step_number}",
            attempts=job.attempts,
            last_error=job.last_error,
        ))
    
    return EmailHistoryResponse(
        lead_id=lead_id,
        email=lead.email,
        events=events,
    )