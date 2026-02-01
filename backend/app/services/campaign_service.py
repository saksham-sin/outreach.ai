"""Campaign service - campaign management and state machine."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignRead,
    CampaignReadWithStats,
)
from app.models.campaign_tag import CampaignTag
from app.models.lead import Lead
from app.models.email_template import EmailTemplate
from app.models.email_job import EmailJob
from app.domain.enums import CampaignStatus, LeadStatus, JobStatus

logger = logging.getLogger(__name__)


class CampaignError(Exception):
    """Custom exception for campaign errors."""
    pass


class CampaignService:
    """Service for campaign management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_campaign(
        self,
        user_id: UUID,
        data: CampaignCreate,
    ) -> Campaign:
        """
        Create a new campaign in DRAFT status.
        
        Args:
            user_id: Owner's user ID
            data: Campaign creation data
            
        Returns:
            Created campaign
        """
        campaign = Campaign(
            user_id=user_id,
            name=data.name,
            pitch=data.pitch,
            tone=data.tone,
            status=CampaignStatus.DRAFT,
        )
        self.session.add(campaign)
        await self.session.flush()
        await self.session.refresh(campaign)
        
        logger.info(f"Created campaign: {campaign.id} - {campaign.name}")
        return campaign

    async def get_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> Optional[Campaign]:
        """Get a campaign by ID, ensuring user ownership."""
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == user_id)
            .options(
                selectinload(Campaign.templates),
                selectinload(Campaign.leads),
            )
        )
        return result.scalar_one_or_none()

    async def get_campaign_with_stats(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> Optional[CampaignReadWithStats]:
        """Get a campaign with computed statistics."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return None
        
        # Get lead counts by status
        lead_stats = await self.session.execute(
            select(
                Lead.status,
                func.count(Lead.id).label("count")
            )
            .where(Lead.campaign_id == campaign_id)
            .group_by(Lead.status)
        )
        
        status_counts = {row.status: row.count for row in lead_stats}
        
        # Get pending job count
        pending_jobs_result = await self.session.execute(
            select(func.count(EmailJob.id))
            .where(
                EmailJob.campaign_id == campaign_id,
                EmailJob.status == JobStatus.PENDING,
            )
        )
        pending_jobs = pending_jobs_result.scalar() or 0
        
        return CampaignReadWithStats(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            pitch=campaign.pitch,
            tone=campaign.tone,
            status=campaign.status,
            start_time=campaign.start_time,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            total_leads=sum(status_counts.values()),
            pending_leads=status_counts.get(LeadStatus.PENDING, 0),
            contacted_leads=status_counts.get(LeadStatus.CONTACTED, 0),
            replied_leads=status_counts.get(LeadStatus.REPLIED, 0),
            failed_leads=status_counts.get(LeadStatus.FAILED, 0),
            pending_jobs=pending_jobs,
        )

    async def list_campaigns(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Campaign]:
        """List all campaigns for a user."""
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.user_id == user_id)
            .order_by(Campaign.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
        data: CampaignUpdate,
    ) -> Optional[Campaign]:
        """
        Update a campaign. Only allowed in DRAFT status.
        
        Args:
            campaign_id: Campaign to update
            user_id: Owner's user ID
            data: Update data
            
        Returns:
            Updated campaign or None if not found
            
        Raises:
            CampaignError: If campaign is not in DRAFT status
        """
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return None
        
        if campaign.status != CampaignStatus.DRAFT:
            raise CampaignError("Can only update campaigns in DRAFT status")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        campaign.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        
        logger.info(f"Updated campaign: {campaign_id}")
        return campaign

    async def launch_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
        start_time: Optional[datetime] = None,
    ) -> Campaign:
        """
        Launch a campaign - transition from DRAFT to ACTIVE.
        Creates initial email jobs for all leads.
        
        Args:
            campaign_id: Campaign to launch
            user_id: Owner's user ID
            start_time: When to start sending emails (defaults to now)
            
        Returns:
            Launched campaign
            
        Raises:
            CampaignError: If campaign cannot be launched
        """
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        if campaign.status != CampaignStatus.DRAFT:
            raise CampaignError("Campaign must be in DRAFT status to launch")
        
        # Verify we have at least one template
        result = await self.session.execute(
            select(EmailTemplate)
            .where(EmailTemplate.campaign_id == campaign_id)
            .order_by(EmailTemplate.step_number)
        )
        templates = list(result.scalars().all())
        
        if not templates:
            raise CampaignError("Campaign must have at least one email template")
        
        # Get all pending leads
        result = await self.session.execute(
            select(Lead)
            .where(
                Lead.campaign_id == campaign_id,
                Lead.status == LeadStatus.PENDING,
            )
        )
        leads = list(result.scalars().all())
        
        if not leads:
            raise CampaignError("Campaign must have at least one lead")
        
        # Use provided start_time or now
        now = datetime.now(timezone.utc)
        scheduled_start = start_time if start_time else now
        
        # Create initial jobs for step 1
        for lead in leads:
            job = EmailJob(
                campaign_id=campaign_id,
                lead_id=lead.id,
                step_number=1,
                scheduled_at=scheduled_start,
                status=JobStatus.PENDING,
            )
            self.session.add(job)
        
        # Update campaign status
        campaign.status = CampaignStatus.ACTIVE
        campaign.start_time = scheduled_start
        campaign.updated_at = now
        
        await self.session.flush()
        
        logger.info(
            f"Launched campaign: {campaign_id} with {len(leads)} leads, "
            f"starting at {scheduled_start}"
        )
        return campaign

    async def pause_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> Campaign:
        """
        Pause an active campaign.
        
        Args:
            campaign_id: Campaign to pause
            user_id: Owner's user ID
            
        Returns:
            Paused campaign
            
        Raises:
            CampaignError: If campaign cannot be paused
        """
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        if not CampaignStatus.can_transition(campaign.status, CampaignStatus.PAUSED):
            raise CampaignError(
                f"Cannot pause campaign in {campaign.status.value} status"
            )
        
        campaign.status = CampaignStatus.PAUSED
        campaign.updated_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        logger.info(f"Paused campaign: {campaign_id}")
        return campaign

    async def resume_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> Campaign:
        """
        Resume a paused campaign.
        
        Args:
            campaign_id: Campaign to resume
            user_id: Owner's user ID
            
        Returns:
            Resumed campaign
            
        Raises:
            CampaignError: If campaign cannot be resumed
        """
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        if campaign.status != CampaignStatus.PAUSED:
            raise CampaignError("Can only resume campaigns in PAUSED status")
        
        campaign.status = CampaignStatus.ACTIVE
        campaign.updated_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        logger.info(f"Resumed campaign: {campaign_id}")
        return campaign

    async def duplicate_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
        new_name: Optional[str] = None,
    ) -> Campaign:
        """
        Duplicate a campaign with all templates (but not leads or jobs).
        
        Args:
            campaign_id: Campaign to duplicate
            user_id: Owner's user ID
            new_name: Optional name for new campaign
            
        Returns:
            New duplicated campaign
            
        Raises:
            CampaignError: If campaign not found
        """
        original = await self.get_campaign(campaign_id, user_id)
        if not original:
            raise CampaignError("Campaign not found")
        
        # Create new campaign
        new_campaign = Campaign(
            user_id=user_id,
            name=new_name or f"{original.name} (Copy)",
            pitch=original.pitch,
            tone=original.tone,
            status=CampaignStatus.DRAFT,
        )
        self.session.add(new_campaign)
        await self.session.flush()
        
        # Duplicate templates
        result = await self.session.execute(
            select(EmailTemplate)
            .where(EmailTemplate.campaign_id == campaign_id)
        )
        templates = result.scalars().all()
        
        for template in templates:
            new_template = EmailTemplate(
                campaign_id=new_campaign.id,
                step_number=template.step_number,
                subject=template.subject,
                body=template.body,
                delay_days=template.delay_days,
            )
            self.session.add(new_template)
        
        await self.session.flush()
        await self.session.refresh(new_campaign)
        
        logger.info(
            f"Duplicated campaign {campaign_id} to {new_campaign.id}"
        )
        return new_campaign

    async def check_campaign_completion(
        self,
        campaign_id: UUID,
    ) -> bool:
        """
        Check if a campaign should be marked as completed.
        Completes if all leads are terminal and no pending jobs.
        
        Args:
            campaign_id: Campaign to check
            
        Returns:
            True if campaign was marked completed
        """
        # Get campaign
        result = await self.session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign or campaign.status != CampaignStatus.ACTIVE:
            return False
        
        # Check for any non-terminal leads
        non_terminal_result = await self.session.execute(
            select(func.count(Lead.id))
            .where(
                Lead.campaign_id == campaign_id,
                Lead.status.in_([LeadStatus.PENDING, LeadStatus.CONTACTED]),
            )
        )
        non_terminal_count = non_terminal_result.scalar() or 0
        
        if non_terminal_count > 0:
            return False
        
        # Check for pending jobs
        pending_jobs_result = await self.session.execute(
            select(func.count(EmailJob.id))
            .where(
                EmailJob.campaign_id == campaign_id,
                EmailJob.status == JobStatus.PENDING,
            )
        )
        pending_jobs = pending_jobs_result.scalar() or 0
        
        if pending_jobs > 0:
            return False
        
        # Mark as completed
        campaign.status = CampaignStatus.COMPLETED
        campaign.updated_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        logger.info(f"Campaign completed: {campaign_id}")
        return True

    async def get_next_send(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> Optional[tuple]:
        """
        Get the next scheduled email send time and job ID.
        
        Args:
            campaign_id: Campaign ID
            user_id: Owner's user ID
            
        Returns:
            Tuple of (next_send_datetime, job_id) or None if no pending jobs
        """
        # Verify campaign exists
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return None
        
        # Get earliest pending job
        result = await self.session.execute(
            select(EmailJob)
            .where(
                EmailJob.campaign_id == campaign_id,
                EmailJob.status == JobStatus.PENDING,
            )
            .order_by(EmailJob.scheduled_at)
            .limit(1)
        )
        job = result.scalar()
        
        if not job:
            return None
        
        return (job.scheduled_at, str(job.id))

    async def send_now(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Trigger immediate send of the next pending email.
        Updates the earliest pending job's scheduled_at to now.
        
        Args:
            campaign_id: Campaign ID
            user_id: Owner's user ID
            
        Returns:
            True if job was updated, False if no pending jobs
        """
        # Verify campaign exists
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        # Get earliest pending job
        result = await self.session.execute(
            select(EmailJob)
            .where(
                EmailJob.campaign_id == campaign_id,
                EmailJob.status == JobStatus.PENDING,
            )
            .order_by(EmailJob.scheduled_at)
            .limit(1)
        )
        job = result.scalar()
        
        if not job:
            return False
        
        # Update to send immediately
        job.scheduled_at = datetime.now(timezone.utc)
        await self.session.flush()
        
        logger.info(f"Triggered immediate send for job: {job.id}")
        return True

    async def delete_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete a campaign.
        
        Only DRAFT campaigns can be deleted.
        Cascade deletes all related leads, templates, and jobs.
        
        Args:
            campaign_id: Campaign ID
            user_id: Owner's user ID
            
        Raises:
            CampaignError: If campaign not found or not in DRAFT status
        """
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        if campaign.status != CampaignStatus.DRAFT:
            raise CampaignError("Only DRAFT campaigns can be deleted")
        
        # Delete all related email jobs first
        await self.session.execute(
            select(EmailJob).where(EmailJob.campaign_id == campaign_id)
        )
        result = await self.session.execute(
            select(EmailJob).where(EmailJob.campaign_id == campaign_id)
        )
        jobs = result.scalars().all()
        for job in jobs:
            await self.session.delete(job)
        
        # Delete all related email templates
        result = await self.session.execute(
            select(EmailTemplate).where(EmailTemplate.campaign_id == campaign_id)
        )
        templates = result.scalars().all()
        for template in templates:
            await self.session.delete(template)
        
        # Delete all related leads
        result = await self.session.execute(
            select(Lead).where(Lead.campaign_id == campaign_id)
        )
        leads = result.scalars().all()
        for lead in leads:
            await self.session.delete(lead)
        
        # Finally delete the campaign itself
        await self.session.delete(campaign)
        await self.session.flush()
        
        logger.info(f"Deleted campaign: {campaign_id}")

    async def add_tag(
        self,
        campaign_id: UUID,
        tag: str,
        user_id: UUID,
    ) -> CampaignTag:
        """
        Add a tag to a campaign.
        
        Args:
            campaign_id: Campaign ID
            tag: Tag string (max 100 chars)
            user_id: Owner's user ID for verification
            
        Returns:
            Created CampaignTag object
            
        Raises:
            CampaignError: If campaign not found or tag already exists
        """
        # Verify campaign ownership
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        # Check if tag already exists
        result = await self.session.execute(
            select(CampaignTag).where(
                (CampaignTag.campaign_id == campaign_id) &
                (CampaignTag.tag == tag.strip())
            )
        )
        if result.scalars().first():
            raise CampaignError("Tag already exists for this campaign")
        
        # Create new tag
        new_tag = CampaignTag(
            campaign_id=campaign_id,
            tag=tag.strip(),
        )
        self.session.add(new_tag)
        await self.session.flush()
        
        logger.info(f"Added tag '{tag}' to campaign {campaign_id}")
        return new_tag

    async def remove_tag(
        self,
        campaign_id: UUID,
        tag: str,
        user_id: UUID,
    ) -> None:
        """
        Remove a tag from a campaign.
        
        Args:
            campaign_id: Campaign ID
            tag: Tag string to remove
            user_id: Owner's user ID for verification
            
        Raises:
            CampaignError: If campaign not found or tag doesn't exist
        """
        # Verify campaign ownership
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise CampaignError("Campaign not found")
        
        # Find and delete the tag
        result = await self.session.execute(
            select(CampaignTag).where(
                (CampaignTag.campaign_id == campaign_id) &
                (CampaignTag.tag == tag.strip())
            )
        )
        tag_obj = result.scalars().first()
        
        if not tag_obj:
            raise CampaignError("Tag not found for this campaign")
        
        await self.session.delete(tag_obj)
        await self.session.flush()
        
        logger.info(f"Removed tag '{tag}' from campaign {campaign_id}")
