"""Email job service - job execution and scheduling."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.email_job import EmailJob, EmailJobCreate
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.email_template import EmailTemplate
from app.models.user import User
from app.domain.enums import JobStatus, LeadStatus, CampaignStatus
from app.infrastructure.email_factory import get_email_provider
from app.infrastructure.email_provider import EmailMetadata, EmailProviderError
from app.core.constants import (
    RETRY_DELAYS_MINUTES,
    WORKER_BATCH_SIZE,
    EmailType,
    RETRY_DELAYS_MINUTES,
    WORKER_BATCH_SIZE,
    MAX_CAMPAIGN_STEPS,
    TEMPLATE_PLACEHOLDERS,
)
from app.core.config import get_settings, get_user_email

logger = logging.getLogger(__name__)
settings = get_settings()


class JobService:
    """Service for email job management and execution."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.email_provider = get_email_provider()

    def _substitute_placeholders(
        self,
        template: str,
        lead: Lead,
    ) -> str:
        """
        Substitute placeholders in template with lead data.
        
        Args:
            template: Template string with placeholders
            lead: Lead with data for substitution
            
        Returns:
            String with placeholders replaced
        """
        result = template
        
        # Substitute first_name
        first_name = lead.first_name or "there"
        result = result.replace(
            TEMPLATE_PLACEHOLDERS["first_name"],
            first_name
        )
        
        # Substitute company
        company = lead.company or "your company"
        result = result.replace(
            TEMPLATE_PLACEHOLDERS["company"],
            company
        )
        
        # Substitute email
        result = result.replace(
            TEMPLATE_PLACEHOLDERS["email"],
            lead.email
        )
        
        return result

    async def get_pending_jobs(
        self,
        limit: int = WORKER_BATCH_SIZE,
    ) -> list[EmailJob]:
        """
        Get jobs that are ready to execute.
        
        Uses FOR UPDATE SKIP LOCKED to ensure atomicity and prevent duplicate sends
        if multiple workers are running concurrently. Only one worker can lock each job.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of pending jobs with scheduled_at <= now, locked by this worker
        """
        now = datetime.now(timezone.utc)
        
        result = await self.session.execute(
            select(EmailJob)
            .where(
                EmailJob.status == JobStatus.PENDING,
                EmailJob.scheduled_at <= now,
            )
            .options(selectinload(EmailJob.lead))
            .order_by(EmailJob.scheduled_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _validate_job_for_execution(
        self,
        job: EmailJob,
    ) -> tuple[bool, str]:
        """
        Validate if a job should be executed.
        
        Args:
            job: Job to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Get lead
        if not job.lead:
            result = await self.session.execute(
                select(Lead).where(Lead.id == job.lead_id)
            )
            job.lead = result.scalar_one_or_none()
        
        if not job.lead:
            return False, "Lead not found"
        
        # Check if lead is in terminal state
        if job.lead.status.is_terminal():
            return False, f"Lead is in terminal state: {job.lead.status.value}"
        
        # Get campaign
        result = await self.session.execute(
            select(Campaign).where(Campaign.id == job.campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return False, "Campaign not found"
        
        # Check if campaign is active
        if campaign.status != CampaignStatus.ACTIVE:
            return False, f"Campaign is not active: {campaign.status.value}"
        
        # Check retry limit
        if job.attempts >= settings.MAX_RETRY_ATTEMPTS:
            return False, f"Max retry attempts ({settings.MAX_RETRY_ATTEMPTS}) exceeded"
        
        return True, "OK"

    async def execute_job(self, job: EmailJob) -> bool:
        """
        Execute a single email job.
        
        Args:
            job: Job to execute
            
        Returns:
            True if successful, False otherwise
        """
        # Validate job
        is_valid, reason = await self._validate_job_for_execution(job)
        
        if not is_valid:
            # If campaign is paused or not active, keep job pending for resume
            if reason.startswith("Campaign is not active"):
                return await self._defer_job(job, reason)

            return await self._skip_job(job, reason, f"Job {job.id} skipped: {reason}")
        
        # Get template
        template = await self._get_template_for_job(job)
        
        if not template:
            return await self._fail_job_missing_template(job)
        
        # Substitute placeholders
        subject = self._substitute_placeholders(template.subject, job.lead)
        body = self._substitute_placeholders(template.body, job.lead)
        
        # Fetch campaign to get user_id
        campaign = await self._get_campaign_for_job(job.campaign_id)
        
        # Default user-specific email (will use fallback if user has no first_name)
        body, user_email_address = await self._apply_user_signature(body, campaign)
        # Second validation right before send to catch reply/state changes
        # (closes race between first validation and actual send)
        is_valid_final, reason_final = await self._validate_job_for_execution(job)
        if not is_valid_final:
            return await self._skip_job(
                job,
                reason_final,
                f"Job {job.id} skipped at final validation: {reason_final}",
            )
        
        metadata = EmailMetadata(
            campaign_id=job.campaign_id,
            lead_id=job.lead_id,
            step_number=job.step_number,
        )
        
        # Send email with exception handling for provider failures
        try:
            result = await self.email_provider.send_email(
                to_email=job.lead.email,
                subject=subject,
                html_body=body,
                metadata=metadata,
                from_email=user_email_address,  # Pass dynamic user email (or None for default)
                email_type=EmailType.OUTREACH,  # Campaign emails use OUTREACH sender
            )
        except Exception as e:
            # Catch any exceptions from provider (HTTP errors, timeout, etc.)
            logger.error(f"Exception during send for job {job.id}: {str(e)}", exc_info=True)
            return await self._handle_send_failure(job, f"Provider error: {str(e)}")
        
        if not result.success:
            return await self._handle_send_failure(job, result.error or "Unknown error")
        
        # Success
        job.status = JobStatus.SENT
        job.sent_at = datetime.now(timezone.utc)
        job.message_id = result.message_id
        job.updated_at = datetime.now(timezone.utc)
        
        # Update lead status
        if job.lead.status == LeadStatus.PENDING:
            job.lead.status = LeadStatus.CONTACTED
            job.lead.updated_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        logger.info(
            f"Job {job.id} sent successfully to {job.lead.email}, "
            f"MessageID: {job.message_id}"
        )
        
        # Schedule next step if applicable
        await self._schedule_next_step(job)
        
        return True

    async def _defer_job(self, job: EmailJob, reason: str) -> bool:
        job.last_error = reason
        job.updated_at = datetime.now(timezone.utc)
        job.scheduled_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.WORKER_POLL_INTERVAL_SECONDS
        )
        await self.session.flush()
        logger.info(f"Job {job.id} deferred: {reason}")
        return False

    async def _skip_job(self, job: EmailJob, reason: str, log_message: str) -> bool:
        job.status = JobStatus.SKIPPED
        job.last_error = reason
        job.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info(log_message)
        return False

    async def _get_template_for_job(self, job: EmailJob) -> Optional[EmailTemplate]:
        result = await self.session.execute(
            select(EmailTemplate)
            .where(
                EmailTemplate.campaign_id == job.campaign_id,
                EmailTemplate.step_number == job.step_number,
            )
        )
        return result.scalar_one_or_none()

    async def _fail_job_missing_template(self, job: EmailJob) -> bool:
        job.status = JobStatus.FAILED
        job.last_error = f"Template not found for step {job.step_number}"
        job.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.error(f"Job {job.id} failed: template not found")
        return False

    async def _get_campaign_for_job(self, campaign_id: UUID) -> Optional[Campaign]:
        campaign_result = await self.session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        return campaign_result.scalar_one_or_none()

    async def _apply_user_signature(
        self,
        body: str,
        campaign: Optional[Campaign],
    ) -> tuple[str, Optional[str]]:
        user_email_address = None

        if not campaign:
            return body, user_email_address

        user_result = await self.session.execute(
            select(User).where(User.id == campaign.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return body, user_email_address

        if user.email_signature:
            body = f"{body}<br><br>{user.email_signature}"

        if user.first_name:
            user_email_address = get_user_email(user.first_name)

        return body, user_email_address

    async def _handle_send_failure(
        self,
        job: EmailJob,
        error: str,
    ) -> bool:
        """
        Handle a failed send attempt.
        
        Args:
            job: Failed job
            error: Error message
            
        Returns:
            False (job failed)
        """
        job.attempts += 1
        job.last_error = error
        job.updated_at = datetime.now(timezone.utc)
        
        if job.attempts >= settings.MAX_RETRY_ATTEMPTS:
            # Max retries reached - mark as failed
            job.status = JobStatus.FAILED
            
            # Mark lead as failed
            if job.lead and not job.lead.status.is_terminal():
                job.lead.status = LeadStatus.FAILED
                job.lead.updated_at = datetime.now(timezone.utc)
            
            logger.error(
                f"Job {job.id} failed permanently after {job.attempts} attempts: {error}"
            )
        else:
            # Schedule retry with exponential backoff
            delay_index = min(job.attempts - 1, len(RETRY_DELAYS_MINUTES) - 1)
            delay_minutes = RETRY_DELAYS_MINUTES[delay_index]
            job.scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
            
            logger.warning(
                f"Job {job.id} attempt {job.attempts} failed, "
                f"retrying in {delay_minutes} minutes: {error}"
            )
        
        await self.session.flush()
        return False

    async def _schedule_next_step(self, completed_job: EmailJob) -> Optional[EmailJob]:
        """
        Schedule the next step in the sequence after a successful send.
        
        Args:
            completed_job: Successfully completed job
            
        Returns:
            Next job if created, None otherwise
        """
        next_step = completed_job.step_number + 1
        
        if next_step > MAX_CAMPAIGN_STEPS:
            # All emails sent - mark lead as completed if not already terminal
            if completed_job.lead and not completed_job.lead.status.is_terminal():
                completed_job.lead.status = LeadStatus.COMPLETED
                completed_job.lead.updated_at = datetime.now(timezone.utc)
                logger.info(f"Lead {completed_job.lead_id} completed all steps in campaign {completed_job.campaign_id}")
            return None
        
        # Check if template exists for next step
        result = await self.session.execute(
            select(EmailTemplate)
            .where(
                EmailTemplate.campaign_id == completed_job.campaign_id,
                EmailTemplate.step_number == next_step,
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            logger.debug(
                f"No template for step {next_step} in campaign {completed_job.campaign_id}"
            )
            # Mark lead as completed since no next step available
            if completed_job.lead and not completed_job.lead.status.is_terminal():
                completed_job.lead.status = LeadStatus.COMPLETED
                completed_job.lead.updated_at = datetime.now(timezone.utc)
                logger.info(f"Lead {completed_job.lead_id} completed all available steps in campaign {completed_job.campaign_id}")
            return None
        
        # Calculate scheduled time
        delay_minutes = template.delay_minutes or (template.delay_days * 1440)
        scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
        
        # Create next job
        next_job = EmailJob(
            campaign_id=completed_job.campaign_id,
            lead_id=completed_job.lead_id,
            step_number=next_step,
            scheduled_at=scheduled_at,
            status=JobStatus.PENDING,
        )
        self.session.add(next_job)
        await self.session.flush()
        
        logger.info(
            f"Scheduled step {next_step} for lead {completed_job.lead_id} "
            f"at {scheduled_at}"
        )
        return next_job

    async def get_jobs_for_campaign(
        self,
        campaign_id: UUID,
        status: Optional[JobStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EmailJob]:
        """
        Get jobs for a campaign.
        
        Args:
            campaign_id: Campaign to get jobs for
            status: Optional status filter
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of jobs
        """
        query = select(EmailJob).where(EmailJob.campaign_id == campaign_id)
        
        if status:
            query = query.where(EmailJob.status == status)
        
        query = query.order_by(EmailJob.scheduled_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_jobs_for_lead(
        self,
        lead_id: UUID,
    ) -> list[EmailJob]:
        """Get all jobs for a lead."""
        result = await self.session.execute(
            select(EmailJob)
            .where(EmailJob.lead_id == lead_id)
            .order_by(EmailJob.step_number)
        )
        return list(result.scalars().all())

    async def retry_failed_job(self, job_id: UUID) -> bool:
        """
        Retry a single failed job.
        
        Args:
            job_id: Job ID to retry
            
        Returns:
            True if job was reset, False otherwise
        """
        result = await self.session.execute(
            select(EmailJob).where(EmailJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        if job.status != JobStatus.FAILED:
            return False
        
        # Reset job for retry
        job.status = JobStatus.PENDING
        job.scheduled_at = datetime.now(timezone.utc)
        job.attempts = 0
        job.last_error = None
        job.updated_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        logger.info(f"Retrying failed job {job_id}")
        return True

    async def retry_all_failed_jobs(self, campaign_id: UUID) -> int:
        """
        Retry all failed jobs for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Number of jobs reset
        """
        result = await self.session.execute(
            select(EmailJob).where(
                EmailJob.campaign_id == campaign_id,
                EmailJob.status == JobStatus.FAILED,
            )
        )
        jobs = list(result.scalars().all())
        
        count = 0
        for job in jobs:
            job.status = JobStatus.PENDING
            job.scheduled_at = datetime.now(timezone.utc)
            job.attempts = 0
            job.last_error = None
            job.updated_at = datetime.now(timezone.utc)
            count += 1
        
        await self.session.flush()
        
        logger.info(f"Retrying {count} failed jobs for campaign {campaign_id}")
        return count

    async def get_failed_jobs(self, campaign_id: UUID) -> list[EmailJob]:
        """
        Get all failed jobs for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of failed email jobs
        """
        result = await self.session.execute(
            select(EmailJob)
            .where(
                EmailJob.campaign_id == campaign_id,
                EmailJob.status == JobStatus.FAILED,
            )
            .options(selectinload(EmailJob.lead))
        )
        return list(result.scalars().all())

    async def get_step_summary(
        self,
        campaign_id: UUID,
    ) -> list[dict]:
        """
        Get aggregated job status for each step in a campaign.
        
        Returns counts of sent, pending, scheduled, failed, skipped for each step.
        Also includes the next scheduled time for pending jobs (only for non-terminal leads).
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of dicts with step_number and status counts
        """
        from sqlalchemy import func, case, and_
        
        # For pending jobs, we need to exclude those for terminal leads
        # Join with Lead to check lead status
        result = await self.session.execute(
            select(
                EmailJob.step_number,
                func.count(case((EmailJob.status == JobStatus.SENT, 1))).label('sent'),
                # Pending: only count if lead is not terminal
                func.count(case((
                    and_(
                        EmailJob.status == JobStatus.PENDING,
                        Lead.status.not_in([LeadStatus.COMPLETED, LeadStatus.REPLIED, LeadStatus.FAILED])
                    ), 1
                ))).label('pending'),
                func.count(case((EmailJob.status == JobStatus.FAILED, 1))).label('failed'),
                func.count(case((EmailJob.status == JobStatus.SKIPPED, 1))).label('skipped'),
                # Next scheduled: only for pending jobs with non-terminal leads
                func.min(case((
                    and_(
                        EmailJob.status == JobStatus.PENDING,
                        Lead.status.not_in([LeadStatus.COMPLETED, LeadStatus.REPLIED, LeadStatus.FAILED])
                    ), EmailJob.scheduled_at
                ))).label('next_scheduled_at'),
            )
            .join(Lead, EmailJob.lead_id == Lead.id)
            .where(EmailJob.campaign_id == campaign_id)
            .group_by(EmailJob.step_number)
            .order_by(EmailJob.step_number)
        )
        
        rows = result.all()
        return [
            {
                'step_number': row.step_number,
                'sent': row.sent or 0,
                'pending': row.pending or 0,
                'failed': row.failed or 0,
                'skipped': row.skipped or 0,
                'next_scheduled_at': row.next_scheduled_at,
            }
            for row in rows
        ]
