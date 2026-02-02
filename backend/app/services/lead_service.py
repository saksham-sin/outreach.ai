"""Lead service - lead management and CSV import."""

import csv
import io
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.lead import Lead, LeadCreate, LeadRead, LeadImportResult
from app.models.campaign import Campaign
from app.services.campaign_service import CampaignService
from app.models.email_job import EmailJob
from app.domain.enums import CampaignStatus, LeadStatus, JobStatus
from app.core.constants import (
    REQUIRED_CSV_COLUMNS,
    OPTIONAL_CSV_COLUMNS,
    MAX_LEADS_PER_IMPORT,
)

logger = logging.getLogger(__name__)

# Simple email validation regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class LeadError(Exception):
    """Custom exception for lead errors."""
    pass


class LeadService:
    """Service for lead management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        return bool(EMAIL_REGEX.match(email.strip().lower()))

    async def create_lead(
        self,
        campaign_id: UUID,
        user_id: UUID,
        data: LeadCreate,
    ) -> Lead:
        """
        Create a single lead for a campaign.
        
        Args:
            campaign_id: Target campaign
            user_id: Owner's user ID (for verification)
            data: Lead data
            
        Returns:
            Created lead
            
        Raises:
            LeadError: If campaign not found or not owned by user or duplicate email
        """
        # Verify campaign ownership and status
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == user_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise LeadError("Campaign not found")
        
        if campaign.status != CampaignStatus.DRAFT:
            raise LeadError("Can only add leads to campaigns in DRAFT status")
        
        if not self._validate_email(data.email):
            raise LeadError(f"Invalid email format: {data.email}")
        
        # Check for duplicate email in campaign
        email_normalized = data.email.strip().lower()
        existing_lead = await self.session.execute(
            select(Lead)
            .where(Lead.campaign_id == campaign_id, Lead.email == email_normalized)
        )
        if existing_lead.scalar_one_or_none():
            raise LeadError(f"Email '{data.email}' already exists in this campaign")
        
        lead = Lead(
            campaign_id=campaign_id,
            email=email_normalized,
            first_name=data.first_name.strip() if data.first_name else None,
            company=data.company.strip() if data.company else None,
            status=LeadStatus.PENDING,
        )
        self.session.add(lead)
        await self.session.flush()
        await self.session.refresh(lead)
        
        logger.info(f"Created lead: {lead.id} for campaign {campaign_id}")
        return lead

    async def delete_lead(
        self,
        lead_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a lead from a campaign.
        
        Args:
            lead_id: Lead ID to delete
            user_id: Owner's user ID
            
        Returns:
            True if deleted, False if not found or cannot be deleted
        """
        # Get lead and verify ownership via campaign
        result = await self.session.execute(
            select(Lead)
            .join(Campaign)
            .where(
                Lead.id == lead_id,
                Campaign.user_id == user_id,
                Campaign.status == CampaignStatus.DRAFT,
            )
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            return False
        
        await self.session.delete(lead)
        await self.session.flush()
        
        logger.info(f"Deleted lead: {lead_id}")
        return True

    async def import_leads_csv(
        self,
        campaign_id: UUID,
        user_id: UUID,
        csv_content: str,
    ) -> LeadImportResult:
        """
        Import leads from CSV content.
        
        CSV must have 'email' column. Optional: 'first_name', 'company'.
        
        Args:
            campaign_id: Target campaign
            user_id: Owner's user ID
            csv_content: CSV file content as string
            
        Returns:
            Import result with counts and errors
            
        Raises:
            LeadError: If campaign not found or invalid
        """
        # Verify campaign ownership and status
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == user_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise LeadError("Campaign not found")
        
        if campaign.status != CampaignStatus.DRAFT:
            raise LeadError("Can only import leads to campaigns in DRAFT status")
        
        # Parse CSV
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
        except Exception as e:
            raise LeadError(f"Invalid CSV format: {str(e)}")
        
        # Normalize column names (lowercase, strip whitespace)
        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]
        
        # Validate required columns
        if not reader.fieldnames or "email" not in reader.fieldnames:
            raise LeadError("CSV must have 'email' column")
        
        # Get existing emails in campaign to avoid duplicates
        existing_result = await self.session.execute(
            select(Lead.email).where(Lead.campaign_id == campaign_id)
        )
        existing_emails = {row[0] for row in existing_result}
        
        imported = 0
        skipped = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            if imported + skipped >= MAX_LEADS_PER_IMPORT:
                errors.append(
                    f"Maximum import limit ({MAX_LEADS_PER_IMPORT}) reached"
                )
                break
            
            email = row.get("email", "").strip().lower()
            
            # Validate email
            if not email:
                errors.append(f"Row {row_num}: Missing email")
                skipped += 1
                continue
            
            if not self._validate_email(email):
                errors.append(f"Row {row_num}: Invalid email format '{email}'")
                skipped += 1
                continue
            
            # Check for duplicate
            if email in existing_emails:
                errors.append(f"Row {row_num}: Duplicate email '{email}'")
                skipped += 1
                continue
            
            # Create lead
            lead = Lead(
                campaign_id=campaign_id,
                email=email,
                first_name=row.get("first_name", "").strip() or None,
                company=row.get("company", "").strip() or None,
                status=LeadStatus.PENDING,
            )
            self.session.add(lead)
            existing_emails.add(email)
            imported += 1
        
        await self.session.flush()
        
        logger.info(
            f"CSV import to campaign {campaign_id}: "
            f"{imported} imported, {skipped} skipped"
        )
        
        return LeadImportResult(
            total_rows=imported + skipped,
            imported=imported,
            skipped=skipped,
            errors=errors[:50],  # Limit error messages
        )

    async def list_leads(
        self,
        campaign_id: UUID,
        user_id: UUID,
        status: Optional[LeadStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Lead]:
        """
        List leads for a campaign.
        
        Args:
            campaign_id: Campaign to list leads for
            user_id: Owner's user ID
            status: Optional status filter
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of leads
        """
        # Verify campaign ownership
        campaign_result = await self.session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == user_id)
        )
        if not campaign_result.scalar_one_or_none():
            raise LeadError("Campaign not found")
        
        query = select(Lead).where(Lead.campaign_id == campaign_id)
        
        if status:
            query = query.where(Lead.status == status)
        
        query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_lead(
        self,
        lead_id: UUID,
        user_id: UUID,
    ) -> Optional[Lead]:
        """Get a lead by ID, verifying user ownership through campaign."""
        result = await self.session.execute(
            select(Lead)
            .join(Campaign)
            .where(Lead.id == lead_id, Campaign.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def copy_leads_from_campaign(
        self,
        source_campaign_id: UUID,
        target_campaign_id: UUID,
        user_id: UUID,
    ) -> int:
        """
        Copy leads from one campaign to another.
        
        Args:
            source_campaign_id: Campaign to copy leads from
            target_campaign_id: Campaign to copy leads to
            user_id: Owner's user ID
            
        Returns:
            Number of leads copied
            
        Raises:
            LeadError: If campaigns not found or target not in DRAFT status
        """
        # Verify source campaign ownership
        source_result = await self.session.execute(
            select(Campaign)
            .where(
                Campaign.id == source_campaign_id,
                Campaign.user_id == user_id,
            )
        )
        if not source_result.scalar_one_or_none():
            raise LeadError("Source campaign not found")
        
        # Verify target campaign ownership and status
        target_result = await self.session.execute(
            select(Campaign)
            .where(
                Campaign.id == target_campaign_id,
                Campaign.user_id == user_id,
            )
        )
        target_campaign = target_result.scalar_one_or_none()
        
        if not target_campaign:
            raise LeadError("Target campaign not found")
        
        if target_campaign.status != CampaignStatus.DRAFT:
            raise LeadError("Can only copy leads to campaigns in DRAFT status")
        
        # Get existing emails in target
        existing_result = await self.session.execute(
            select(Lead.email).where(Lead.campaign_id == target_campaign_id)
        )
        existing_emails = {row[0] for row in existing_result}
        
        # Get source leads
        source_leads_result = await self.session.execute(
            select(Lead).where(Lead.campaign_id == source_campaign_id)
        )
        source_leads = source_leads_result.scalars().all()
        
        copied = 0
        for lead in source_leads:
            if lead.email not in existing_emails:
                new_lead = Lead(
                    campaign_id=target_campaign_id,
                    email=lead.email,
                    first_name=lead.first_name,
                    company=lead.company,
                    status=LeadStatus.PENDING,
                )
                self.session.add(new_lead)
                existing_emails.add(lead.email)
                copied += 1
        
        await self.session.flush()
        
        logger.info(
            f"Copied {copied} leads from campaign {source_campaign_id} "
            f"to {target_campaign_id}"
        )
        return copied

    async def mark_lead_replied(self, lead_id: UUID) -> Optional[Lead]:
        """
        Mark a lead as replied (terminal state).
        Called when an inbound reply is detected.
        Also cancels all pending jobs for this lead.
        
        Args:
            lead_id: Lead to mark
            
        Returns:
            Updated lead or None if not found
        """
        result = await self.session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            return None
        
        # Only update if not already terminal
        if not lead.status.is_terminal():
            lead.status = LeadStatus.REPLIED
            lead.updated_at = datetime.now(timezone.utc)
            
            # Cancel all pending jobs for this lead
            pending_jobs_result = await self.session.execute(
                select(EmailJob).where(
                    EmailJob.lead_id == lead_id,
                    EmailJob.status == JobStatus.PENDING,
                )
            )
            pending_jobs = pending_jobs_result.scalars().all()
            
            for job in pending_jobs:
                job.status = JobStatus.SKIPPED
                job.last_error = "Lead replied - job canceled"
                job.updated_at = datetime.now(timezone.utc)
            
            await self.session.flush()

            # Check if campaign can be completed now
            try:
                campaign_service = CampaignService(self.session)
                await campaign_service.check_campaign_completion(lead.campaign_id)
            except Exception:
                logger.exception(f"Failed to check campaign completion after reply for lead {lead_id}")

            logger.info(f"Lead marked as replied: {lead_id}, canceled {len(pending_jobs)} pending jobs")
        
        return lead

    async def mark_lead_failed(self, lead_id: UUID) -> Optional[Lead]:
        """
        Mark a lead as failed (terminal state).
        Called when all email attempts have failed.
        
        Args:
            lead_id: Lead to mark
            
        Returns:
            Updated lead or None if not found
        """
        result = await self.session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            return None
        
        # Only update if not already terminal
        if not lead.status.is_terminal():
            lead.status = LeadStatus.FAILED
            lead.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            
            logger.info(f"Lead marked as failed: {lead_id}")
        
        return lead
