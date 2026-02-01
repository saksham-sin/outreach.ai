"""Email template model - templates per campaign step."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class EmailTemplateBase(SQLModel):
    """Base email template fields."""
    
    step_number: int = Field(ge=1, le=3)  # 1-3
    subject: str = Field(max_length=200)
    body: str = Field(max_length=10000)  # HTML body
    delay_days: int = Field(default=0, ge=0)  # Days to wait before sending (for steps > 1)


class EmailTemplate(EmailTemplateBase, table=True):
    """Email template database model."""
    
    __tablename__ = "email_templates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaigns.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="templates")


class EmailTemplateCreate(SQLModel):
    """Schema for creating an email template."""
    
    step_number: int = Field(ge=1, le=3)
    subject: str
    body: str
    delay_days: int = 0


class EmailTemplateUpdate(SQLModel):
    """Schema for updating an email template."""
    
    subject: Optional[str] = None
    body: Optional[str] = None
    delay_days: Optional[int] = None


class EmailTemplateRead(EmailTemplateBase):
    """Schema for reading an email template."""
    
    id: UUID
    campaign_id: UUID
    created_at: datetime
    updated_at: datetime
