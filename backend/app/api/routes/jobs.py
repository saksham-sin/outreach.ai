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


class StepSummary(BaseModel):
    """Summary of job statuses for a single step."""
    step_number: int
    sent: int
    pending: int
    failed: int
    skipped: int
    next_scheduled_at: str | None = None


@router.get(
    "/campaigns/{campaign_id}/step-summary",
    response_model=list[StepSummary],
    summary="Get job status summary per step",
    description="Get aggregated job counts by status for each step in a campaign.",
)
async def get_step_summary(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[StepSummary]:
    """
    Get job status summary for each step.
    
    Returns counts of sent, pending, failed, skipped jobs per step,
    along with the next scheduled send time for pending jobs.
    """
    service = JobService(session)
    
    summaries = await service.get_step_summary(campaign_id)
    
    return [
        StepSummary(
            step_number=s['step_number'],
            sent=s['sent'],
            pending=s['pending'],
            failed=s['failed'],
            skipped=s['skipped'],
            next_scheduled_at=s['next_scheduled_at'].isoformat() if s['next_scheduled_at'] else None,
        )
        for s in summaries
    ]


class LeadJobInfo(BaseModel):
    """Job information for a lead."""
    job_id: str
    step_number: int
    status: str
    scheduled_at: str | None = None
    sent_at: str | None = None


@router.get(
    "/leads/{lead_id}/jobs",
    response_model=list[LeadJobInfo],
    summary="Get jobs for a lead",
    description="Get all jobs for a specific lead with their statuses.",
)
async def get_jobs_for_lead(
    lead_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[LeadJobInfo]:
    """
    Get all jobs for a lead.
    
    Returns job details for each step, including status and timing info.
    """
    service = JobService(session)
    
    jobs = await service.get_jobs_for_lead(lead_id)
    
    return [
        LeadJobInfo(
            job_id=str(job.id),
            step_number=job.step_number,
            status=job.status.value,
            scheduled_at=job.scheduled_at.isoformat() if job.scheduled_at else None,
            sent_at=job.sent_at.isoformat() if job.sent_at else None,
        )
        for job in jobs
    ]
