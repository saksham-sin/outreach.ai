"""Email template service - template management and AI generation."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.email_template import (
    EmailTemplate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
)
from app.models.campaign import Campaign
from app.domain.enums import CampaignStatus
from app.infrastructure.llm import get_llm_client, GeneratedEmail
from app.core.constants import DEFAULT_STEP_DELAYS, MAX_CAMPAIGN_STEPS

logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """Custom exception for template errors."""
    pass


class TemplateService:
    """Service for email template management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm = get_llm_client()

    @staticmethod
    def _resolve_delay_minutes(
        delay_minutes: Optional[int],
        delay_days: Optional[int],
    ) -> int:
        """Resolve delay in minutes from minutes or days input."""
        if delay_minutes is not None:
            return max(0, delay_minutes)
        if delay_days is not None:
            return max(0, delay_days * 1440)
        return 0

    async def _get_campaign(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> Campaign:
        """Get and validate campaign ownership."""
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == user_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise TemplateError("Campaign not found")
        
        return campaign

    async def create_template(
        self,
        campaign_id: UUID,
        user_id: UUID,
        data: EmailTemplateCreate,
    ) -> EmailTemplate:
        """
        Create an email template manually.
        
        Args:
            campaign_id: Target campaign
            user_id: Owner's user ID
            data: Template data
            
        Returns:
            Created template
            
        Raises:
            TemplateError: If validation fails
        """
        campaign = await self._get_campaign(campaign_id, user_id)
        
        if campaign.status != CampaignStatus.DRAFT:
            raise TemplateError("Can only add templates to campaigns in DRAFT status")
        
        if data.step_number > MAX_CAMPAIGN_STEPS:
            raise TemplateError(f"Maximum {MAX_CAMPAIGN_STEPS} steps allowed")
        
        # Check if template for this step already exists
        existing = await self.session.execute(
            select(EmailTemplate)
            .where(
                EmailTemplate.campaign_id == campaign_id,
                EmailTemplate.step_number == data.step_number,
            )
        )
        if existing.scalar_one_or_none():
            raise TemplateError(
                f"Template for step {data.step_number} already exists"
            )
        
        template = EmailTemplate(
            campaign_id=campaign_id,
            step_number=data.step_number,
            subject=data.subject,
            body=data.body,
            delay_minutes=self._resolve_delay_minutes(
                data.delay_minutes,
                data.delay_days,
            ),
            delay_days=(
                self._resolve_delay_minutes(data.delay_minutes, data.delay_days) // 1440
            ),
        )
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        
        logger.info(
            f"Created template for campaign {campaign_id}, step {data.step_number}"
        )
        return template

    async def get_template(
        self,
        template_id: UUID,
        user_id: UUID,
    ) -> Optional[EmailTemplate]:
        """Get a template by ID, verifying user ownership."""
        result = await self.session.execute(
            select(EmailTemplate)
            .join(Campaign)
            .where(EmailTemplate.id == template_id, Campaign.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_template_by_step(
        self,
        campaign_id: UUID,
        step_number: int,
    ) -> Optional[EmailTemplate]:
        """Get a template by campaign and step number."""
        result = await self.session.execute(
            select(EmailTemplate)
            .where(
                EmailTemplate.campaign_id == campaign_id,
                EmailTemplate.step_number == step_number,
            )
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        campaign_id: UUID,
        user_id: UUID,
    ) -> list[EmailTemplate]:
        """List all templates for a campaign."""
        # Verify ownership
        await self._get_campaign(campaign_id, user_id)
        
        result = await self.session.execute(
            select(EmailTemplate)
            .where(EmailTemplate.campaign_id == campaign_id)
            .order_by(EmailTemplate.step_number)
        )
        return list(result.scalars().all())

    async def update_template(
        self,
        template_id: UUID,
        user_id: UUID,
        data: EmailTemplateUpdate,
    ) -> Optional[EmailTemplate]:
        """
        Update a template. Allowed in DRAFT status only.
        
        Args:
            template_id: Template to update
            user_id: Owner's user ID
            data: Update data
            
        Returns:
            Updated template
            
        Raises:
            TemplateError: If campaign not in DRAFT status
        """
        result = await self.session.execute(
            select(EmailTemplate)
            .join(Campaign)
            .where(EmailTemplate.id == template_id, Campaign.user_id == user_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        # Get campaign to check status
        campaign_result = await self.session.execute(
            select(Campaign).where(Campaign.id == template.campaign_id)
        )
        campaign = campaign_result.scalar_one()
        
        if campaign.status != CampaignStatus.DRAFT:
            raise TemplateError(
                "Can only update templates for campaigns in DRAFT status"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        if "delay_minutes" in update_data or "delay_days" in update_data:
            resolved_minutes = self._resolve_delay_minutes(
                update_data.get("delay_minutes"),
                update_data.get("delay_days"),
            )
            update_data["delay_minutes"] = resolved_minutes
            update_data["delay_days"] = resolved_minutes // 1440
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        
        logger.info(f"Updated template: {template_id}")
        return template

    async def generate_template(
        self,
        campaign_id: UUID,
        user_id: UUID,
        step_number: int,
    ) -> EmailTemplate:
        """
        Generate an email template using AI for a specific step.
        Creates or replaces the template for that step.
        
        Args:
            campaign_id: Target campaign
            user_id: Owner's user ID
            step_number: Step number (1-3)
            
        Returns:
            Generated template
            
        Raises:
            TemplateError: If validation fails
        """
        campaign = await self._get_campaign(campaign_id, user_id)
        
        if campaign.status != CampaignStatus.DRAFT:
            raise TemplateError(
                "Can only generate templates for campaigns in DRAFT status"
            )
        
        if step_number > MAX_CAMPAIGN_STEPS:
            raise TemplateError(f"Maximum {MAX_CAMPAIGN_STEPS} steps allowed")
        
        # Check if leads have company data
        from app.models.lead import Lead
        result = await self.session.execute(
            select(Lead).where(Lead.campaign_id == campaign_id)
        )
        leads = list(result.scalars().all())
        
        # Determine if all leads have company or none have company
        has_company = None
        if leads:
            leads_with_company = [l for l in leads if l.company and l.company.strip()]
            if len(leads_with_company) == len(leads):
                # All leads have company
                has_company = True
            elif len(leads_with_company) == 0:
                # No leads have company
                has_company = False
            # If mixed, we'll default to True (include company placeholder)
            else:
                has_company = True
        
        # Get previous step's subject for follow-up context
        previous_subject = None
        if step_number > 1:
            prev_template = await self.get_template_by_step(
                campaign_id, step_number - 1
            )
            if prev_template:
                previous_subject = prev_template.subject
        
        # Generate email using LLM
        generated: GeneratedEmail = await self.llm.generate_email(
            campaign_name=campaign.name,
            pitch=campaign.pitch,
            step_number=step_number,
            tone=campaign.tone,
            previous_subject=previous_subject,
            has_company=has_company,
        )
        
        # Check if template exists for this step
        existing = await self.get_template_by_step(campaign_id, step_number)
        
        if existing:
            # Update existing template
            existing.subject = generated.subject
            existing.body = generated.body
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            
            logger.info(
                f"Regenerated template for campaign {campaign_id}, step {step_number}"
            )
            return existing
        else:
            # Create new template
            template = EmailTemplate(
                campaign_id=campaign_id,
                step_number=step_number,
                subject=generated.subject,
                body=generated.body,
                delay_minutes=DEFAULT_STEP_DELAYS.get(step_number, 3) * 1440,
                delay_days=DEFAULT_STEP_DELAYS.get(step_number, 3),
            )
            self.session.add(template)
            await self.session.flush()
            await self.session.refresh(template)
            
            logger.info(
                f"Generated new template for campaign {campaign_id}, step {step_number}"
            )
            return template

    async def rewrite_template(
        self,
        template_id: UUID,
        user_id: UUID,
        instructions: str,
    ) -> EmailTemplate:
        """
        Rewrite an existing template using AI based on instructions.
        
        Args:
            template_id: Template to rewrite
            user_id: Owner's user ID
            instructions: Rewrite instructions
            
        Returns:
            Rewritten template
            
        Raises:
            TemplateError: If validation fails
        """
        result = await self.session.execute(
            select(EmailTemplate)
            .join(Campaign)
            .where(EmailTemplate.id == template_id, Campaign.user_id == user_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise TemplateError("Template not found")
        
        # Get campaign
        campaign_result = await self.session.execute(
            select(Campaign).where(Campaign.id == template.campaign_id)
        )
        campaign = campaign_result.scalar_one()
        
        if campaign.status != CampaignStatus.DRAFT:
            raise TemplateError(
                "Can only rewrite templates for campaigns in DRAFT status"
            )
        
        # Check if leads have company data
        from app.models.lead import Lead
        result = await self.session.execute(
            select(Lead).where(Lead.campaign_id == template.campaign_id)
        )
        leads = list(result.scalars().all())
        
        # Determine if all leads have company or none have company
        has_company = None
        if leads:
            leads_with_company = [l for l in leads if l.company and l.company.strip()]
            if len(leads_with_company) == len(leads):
                # All leads have company
                has_company = True
            elif len(leads_with_company) == 0:
                # No leads have company
                has_company = False
            # If mixed, default to True
            else:
                has_company = True
        
        # Rewrite using LLM
        generated: GeneratedEmail = await self.llm.rewrite_email(
            current_subject=template.subject,
            current_body=template.body,
            instructions=instructions,
            campaign_name=campaign.name,
            pitch=campaign.pitch,
            step_number=template.step_number,
            tone=campaign.tone,
            has_company=has_company,
        )
        
        # Update template
        template.subject = generated.subject
        template.body = generated.body
        template.updated_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        logger.info(f"Rewrote template: {template_id}")
        return template

    async def generate_all_templates(
        self,
        campaign_id: UUID,
        user_id: UUID,
        num_steps: int = 3,
    ) -> list[EmailTemplate]:
        """
        Generate all templates for a campaign (up to num_steps).
        
        Args:
            campaign_id: Target campaign
            user_id: Owner's user ID
            num_steps: Number of steps to generate (1-3)
            
        Returns:
            List of generated templates
        """
        if num_steps > MAX_CAMPAIGN_STEPS:
            num_steps = MAX_CAMPAIGN_STEPS
        
        templates = []
        for step in range(1, num_steps + 1):
            template = await self.generate_template(campaign_id, user_id, step)
            templates.append(template)
        
        return templates
