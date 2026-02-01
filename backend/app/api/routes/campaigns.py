"""Campaign API routes."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from app.api.dependencies import SessionDep, CurrentUser
from app.services.campaign_service import CampaignService, CampaignError
from app.infrastructure.llm import get_llm_client
from app.models.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignRead,
    CampaignReadWithStats,
)
from app.domain.enums import CampaignStatus

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class TagRequest(BaseModel):
    """Request to add or remove a tag."""
    tag: str


class DuplicateCampaignRequest(BaseModel):
    """Request to duplicate a campaign."""
    new_name: Optional[str] = None


class EnhancePitchRequest(BaseModel):
    """Request to enhance a campaign pitch."""
    name: str
    pitch: str


class EnhancePitchResponse(BaseModel):
    """Response containing enhanced pitch."""
    pitch: str


class LaunchCampaignRequest(BaseModel):
    """Request to launch a campaign."""
    start_time: Optional[datetime] = None  # ISO datetime; if None, sends immediately


class NextSendResponse(BaseModel):
    """Response containing next send time."""
    next_send_at: Optional[datetime] = None
    job_id: Optional[str] = None


class CampaignListResponse(BaseModel):
    """Response containing list of campaigns."""
    campaigns: list[CampaignRead]
    total: int


@router.post(
    "",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create campaign",
    description="Create a new campaign in DRAFT status.",
)
async def create_campaign(
    data: CampaignCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignRead:
    """
    Create a new outreach campaign.
    
    The campaign is created in DRAFT status. Add leads and templates
    before launching.
    """
    service = CampaignService(session)
    campaign = await service.create_campaign(current_user.id, data)
    
    return CampaignRead(
        id=campaign.id,
        user_id=campaign.user_id,
        name=campaign.name,
        pitch=campaign.pitch,
        tone=campaign.tone,
        status=campaign.status,
        start_time=campaign.start_time,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.post(
    "/enhance-pitch",
    response_model=EnhancePitchResponse,
    summary="Enhance pitch with AI",
    description="Improve a campaign pitch using AI.",
)
async def enhance_pitch(
    data: EnhancePitchRequest,
    current_user: CurrentUser,
) -> EnhancePitchResponse:
    """
    Enhance a campaign pitch using AI.

    Requires authentication but does not require a campaign to exist yet.
    """
    if not data.pitch.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pitch is required",
        )

    if len(data.pitch) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pitch must be less than 2000 characters",
        )

    campaign_name = data.name.strip() or "Campaign"
    llm = get_llm_client()

    try:
        enhanced_pitch = await llm.enhance_pitch(campaign_name, data.pitch)
        return EnhancePitchResponse(pitch=enhanced_pitch)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enhance pitch",
        )


@router.get(
    "",
    response_model=CampaignListResponse,
    summary="List campaigns",
    description="List all campaigns for the current user.",
)
async def list_campaigns(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> CampaignListResponse:
    """
    List all campaigns for the current user.
    
    Supports pagination with skip and limit parameters.
    """
    service = CampaignService(session)
    campaigns = await service.list_campaigns(current_user.id, skip, limit)
    
    return CampaignListResponse(
        campaigns=[
            CampaignRead(
                id=c.id,
                user_id=c.user_id,
                name=c.name,
                pitch=c.pitch,
                tone=c.tone,
                status=c.status,
                start_time=c.start_time,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in campaigns
        ],
        total=len(campaigns),
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignReadWithStats,
    summary="Get campaign",
    description="Get a campaign with statistics.",
)
async def get_campaign(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignReadWithStats:
    """
    Get a campaign with computed statistics.
    
    Includes lead counts by status and pending job count.
    """
    service = CampaignService(session)
    campaign = await service.get_campaign_with_stats(campaign_id, current_user.id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    
    return campaign


@router.patch(
    "/{campaign_id}",
    response_model=CampaignRead,
    summary="Update campaign",
    description="Update a campaign. Only allowed in DRAFT status.",
)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignRead:
    """
    Update a campaign.
    
    Only campaigns in DRAFT status can be updated.
    """
    service = CampaignService(session)
    
    try:
        campaign = await service.update_campaign(campaign_id, current_user.id, data)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )
        
        return CampaignRead(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            pitch=campaign.pitch,
            tone=campaign.tone,
            status=campaign.status,
            start_time=campaign.start_time,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{campaign_id}/launch",
    response_model=CampaignRead,
    summary="Launch campaign",
    description="Launch a campaign - transition from DRAFT to ACTIVE.",
)
async def launch_campaign(
    campaign_id: UUID,
    data: LaunchCampaignRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignRead:
    """
    Launch a campaign.
    
    The campaign must be in DRAFT status with at least one lead
    and one template.
    
    Request body:
    - start_time (optional): ISO datetime when to start sending emails.
                             If omitted, sends immediately.
    """
    service = CampaignService(session)
    
    try:
        campaign = await service.launch_campaign(
            campaign_id,
            current_user.id,
            start_time=data.start_time,
        )
        
        return CampaignRead(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            pitch=campaign.pitch,
            tone=campaign.tone,
            status=campaign.status,
            start_time=campaign.start_time,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{campaign_id}/pause",
    response_model=CampaignRead,
    summary="Pause campaign",
    description="Pause an active campaign.",
)
async def pause_campaign(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignRead:
    """
    Pause an active campaign.
    
    Pending email jobs will not be sent while paused.
    """
    service = CampaignService(session)
    
    try:
        campaign = await service.pause_campaign(campaign_id, current_user.id)
        
        return CampaignRead(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            pitch=campaign.pitch,
            tone=campaign.tone,
            status=campaign.status,
            start_time=campaign.start_time,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{campaign_id}/resume",
    response_model=CampaignRead,
    summary="Resume campaign",
    description="Resume a paused campaign.",
)
async def resume_campaign(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignRead:
    """
    Resume a paused campaign.
    
    Pending email jobs will start being processed again.
    """
    service = CampaignService(session)
    
    try:
        campaign = await service.resume_campaign(campaign_id, current_user.id)
        
        return CampaignRead(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            pitch=campaign.pitch,
            tone=campaign.tone,
            status=campaign.status,
            start_time=campaign.start_time,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{campaign_id}/duplicate",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate campaign",
    description="Duplicate a campaign with all templates.",
)
async def duplicate_campaign(
    campaign_id: UUID,
    request: DuplicateCampaignRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> CampaignRead:
    """
    Duplicate a campaign.
    
    Creates a new campaign with copied templates but no leads or jobs.
    """
    service = CampaignService(session)
    
    try:
        campaign = await service.duplicate_campaign(
            campaign_id, current_user.id, request.new_name
        )
        
        return CampaignRead(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            pitch=campaign.pitch,
            tone=campaign.tone,
            status=campaign.status,
            start_time=campaign.start_time,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{campaign_id}/next-send",
    response_model=NextSendResponse,
    summary="Get next send time",
    description="Get the scheduled time of the next email to be sent.",
)
async def get_next_send(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> NextSendResponse:
    """
    Get the next scheduled email send time for a campaign.
    
    Returns None if no pending emails are scheduled.
    """
    service = CampaignService(session)
    
    result = await service.get_next_send(campaign_id, current_user.id)
    
    if not result:
        return NextSendResponse(next_send_at=None, job_id=None)
    
    next_send_at, job_id = result
    return NextSendResponse(next_send_at=next_send_at, job_id=job_id)


@router.post(
    "/{campaign_id}/send-now",
    response_model=dict,
    summary="Send next email immediately",
    description="Trigger immediate send of the next pending email.",
)
async def send_now(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Trigger immediate send of the next pending email.
    
    Updates the earliest pending job to send immediately.
    """
    service = CampaignService(session)
    
    try:
        success = await service.send_now(campaign_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending emails to send",
            )
        
        return {"success": True, "message": "Next email scheduled to send immediately"}
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a campaign",
    description="Delete a campaign (only DRAFT campaigns can be deleted).",
)
async def delete_campaign(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """
    Delete a campaign.
    
    Only campaigns in DRAFT status can be deleted.
    """
    service = CampaignService(session)
    
    try:
        await service.delete_campaign(campaign_id, current_user.id)
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post(
    "/{campaign_id}/tags",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add tag to campaign",
    description="Add a tag to a campaign.",
)
async def add_tag(
    campaign_id: UUID,
    request: TagRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Add a tag to a campaign.
    
    Tags help organize and categorize campaigns.
    """
    service = CampaignService(session)
    
    try:
        await service.add_tag(campaign_id, request.tag, current_user.id)
        await session.commit()
        return {"success": True, "message": f"Tag '{request.tag}' added"}
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{campaign_id}/tags/{tag}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove tag from campaign",
    description="Remove a tag from a campaign.",
)
async def remove_tag(
    campaign_id: UUID,
    tag: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """
    Remove a tag from a campaign.
    
    The tag string is URL-encoded in the path.
    """
    service = CampaignService(session)
    
    try:
        await service.remove_tag(campaign_id, tag, current_user.id)
        await session.commit()
    except CampaignError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )