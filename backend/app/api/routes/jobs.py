"""Email jobs API routes."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import SessionDep, CurrentUser
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class FailedJobInfo(BaseModel):
    """Information about a failed job."""
    job_id: str
    lead_id: str


@router.post(
    "/{job_id}/retry",
    summary="Retry a failed job",
    description="Reset a failed job to retry sending the email.",
)
async def retry_job(
    job_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Retry a single failed job.
    
    The job will be reset to PENDING status and scheduled for immediate execution.
    """
    service = JobService(session)
    
    success = await service.retry_failed_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not in failed status",
        )
    
    return {"success": True, "message": "Job reset for retry"}


@router.post(
    "/campaigns/{campaign_id}/retry-all",
    summary="Retry all failed jobs for a campaign",
    description="Reset all failed jobs for a campaign to retry sending emails.",
)
async def retry_all_failed_jobs(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Retry all failed jobs for a campaign.
    
    All failed jobs will be reset to PENDING status and scheduled for immediate execution.
    """
    service = JobService(session)
    
    count = await service.retry_all_failed_jobs(campaign_id)
    
    return {"success": True, "message": f"Reset {count} failed jobs for retry"}


@router.get(
    "/campaigns/{campaign_id}/failed",
    response_model=list[FailedJobInfo],
    summary="Get failed jobs for a campaign",
    description="Retrieve all failed jobs for a campaign with lead mapping.",
)
async def get_failed_jobs(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[FailedJobInfo]:
    """
    Get all failed jobs for a campaign.
    
    Returns a list of failed jobs with their job_id and lead_id for mapping.
    """
    service = JobService(session)
    
    jobs = await service.get_failed_jobs(campaign_id)
    
    return [
        FailedJobInfo(job_id=str(job.id), lead_id=str(job.lead_id))
        for job in jobs
    ]
