"""Email template API routes."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from app.api.dependencies import SessionDep, CurrentUser
from app.services.template_service import TemplateService, TemplateError
from app.models.email_template import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateRead,
)

router = APIRouter(prefix="/campaigns/{campaign_id}/templates", tags=["Templates"])


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""
    templates: list[EmailTemplateRead]


class GenerateTemplateRequest(BaseModel):
    """Request to generate a template using AI."""
    step_number: int


class GenerateAllTemplatesRequest(BaseModel):
    """Request to generate all templates."""
    num_steps: int = 3


class RewriteTemplateRequest(BaseModel):
    """Request to rewrite a template using AI."""
    instructions: str


@router.post(
    "",
    response_model=EmailTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    description="Create an email template manually.",
)
async def create_template(
    campaign_id: UUID,
    data: EmailTemplateCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmailTemplateRead:
    """
    Create an email template manually.
    
    The campaign must be in DRAFT status.
    """
    service = TemplateService(session)
    
    try:
        template = await service.create_template(campaign_id, current_user.id, data)
        
        return EmailTemplateRead(
            id=template.id,
            campaign_id=template.campaign_id,
            step_number=template.step_number,
            subject=template.subject,
            body=template.body,
            delay_days=template.delay_days,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=TemplateListResponse,
    summary="List templates",
    description="List all templates for a campaign.",
)
async def list_templates(
    campaign_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> TemplateListResponse:
    """List all templates for a campaign, ordered by step number."""
    service = TemplateService(session)
    
    try:
        templates = await service.list_templates(campaign_id, current_user.id)
        
        return TemplateListResponse(
            templates=[
                EmailTemplateRead(
                    id=t.id,
                    campaign_id=t.campaign_id,
                    step_number=t.step_number,
                    subject=t.subject,
                    body=t.body,
                    delay_days=t.delay_days,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in templates
            ]
        )
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{template_id}",
    response_model=EmailTemplateRead,
    summary="Get template",
    description="Get a single template by ID.",
)
async def get_template(
    campaign_id: UUID,
    template_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmailTemplateRead:
    """Get a single template by ID."""
    service = TemplateService(session)
    template = await service.get_template(template_id, current_user.id)
    
    if not template or template.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    
    return EmailTemplateRead(
        id=template.id,
        campaign_id=template.campaign_id,
        step_number=template.step_number,
        subject=template.subject,
        body=template.body,
        delay_days=template.delay_days,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch(
    "/{template_id}",
    response_model=EmailTemplateRead,
    summary="Update template",
    description="Update a template. Only allowed in DRAFT status.",
)
async def update_template(
    campaign_id: UUID,
    template_id: UUID,
    data: EmailTemplateUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmailTemplateRead:
    """
    Update a template.
    
    The campaign must be in DRAFT status.
    """
    service = TemplateService(session)
    
    try:
        template = await service.update_template(template_id, current_user.id, data)
        
        if not template or template.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        
        return EmailTemplateRead(
            id=template.id,
            campaign_id=template.campaign_id,
            step_number=template.step_number,
            subject=template.subject,
            body=template.body,
            delay_days=template.delay_days,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/generate",
    response_model=EmailTemplateRead,
    summary="Generate template with AI",
    description="Generate an email template using AI for a specific step.",
)
async def generate_template(
    campaign_id: UUID,
    request: GenerateTemplateRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmailTemplateRead:
    """
    Generate an email template using AI.
    
    Uses the campaign's pitch and tone to generate an appropriate email.
    Creates or replaces the template for the specified step.
    """
    service = TemplateService(session)
    
    try:
        template = await service.generate_template(
            campaign_id, current_user.id, request.step_number
        )
        
        return EmailTemplateRead(
            id=template.id,
            campaign_id=template.campaign_id,
            step_number=template.step_number,
            subject=template.subject,
            body=template.body,
            delay_days=template.delay_days,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/generate-all",
    response_model=TemplateListResponse,
    summary="Generate all templates with AI",
    description="Generate all email templates (1-3 steps) using AI.",
)
async def generate_all_templates(
    campaign_id: UUID,
    request: GenerateAllTemplatesRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> TemplateListResponse:
    """
    Generate all templates for a campaign using AI.
    
    Generates templates for steps 1 through num_steps (max 3).
    """
    service = TemplateService(session)
    
    try:
        templates = await service.generate_all_templates(
            campaign_id, current_user.id, request.num_steps
        )
        
        return TemplateListResponse(
            templates=[
                EmailTemplateRead(
                    id=t.id,
                    campaign_id=t.campaign_id,
                    step_number=t.step_number,
                    subject=t.subject,
                    body=t.body,
                    delay_days=t.delay_days,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in templates
            ]
        )
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{template_id}/rewrite",
    response_model=EmailTemplateRead,
    summary="Rewrite template with AI",
    description="Rewrite an existing template using AI based on instructions.",
)
async def rewrite_template(
    campaign_id: UUID,
    template_id: UUID,
    request: RewriteTemplateRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmailTemplateRead:
    """
    Rewrite an existing template using AI.
    
    Provide instructions for how the template should be changed.
    """
    service = TemplateService(session)
    
    try:
        template = await service.rewrite_template(
            template_id, current_user.id, request.instructions
        )
        
        if template.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        
        return EmailTemplateRead(
            id=template.id,
            campaign_id=template.campaign_id,
            step_number=template.step_number,
            subject=template.subject,
            body=template.body,
            delay_days=template.delay_days,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
