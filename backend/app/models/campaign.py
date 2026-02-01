"""Campaign model - one-off execution unit for outreach."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from uuid import UUID, uuid4

from app.domain.enums import CampaignStatus, EmailTone

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.email_template import EmailTemplate
    from app.models.campaign_tag import CampaignTag


class CampaignBase(SQLModel):
    """Base campaign fields."""
    
    name: str = Field(max_length=255)
    pitch: str = Field(max_length=2000)  # Value proposition / campaign pitch
    tone: EmailTone = Field(default=EmailTone.PROFESSIONAL)


class Campaign(CampaignBase, table=True):
    """Campaign database model."""
    
    __tablename__ = "campaigns"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, index=True)
    start_time: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    leads: list["Lead"] = Relationship(back_populates="campaign")
    templates: list["EmailTemplate"] = Relationship(back_populates="campaign")
    tags: list["CampaignTag"] = Relationship(back_populates="campaign")


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign."""
    pass


class CampaignUpdate(SQLModel):
    """Schema for updating a campaign."""
    
    name: Optional[str] = None
    pitch: Optional[str] = None
    tone: Optional[EmailTone] = None


class CampaignRead(CampaignBase):
    """Schema for reading a campaign."""
    
    id: UUID
    user_id: UUID
    status: CampaignStatus
    start_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []  # List of tag strings


class CampaignReadWithStats(CampaignRead):
    """Schema for reading a campaign with statistics."""
    
    total_leads: int = 0
    pending_leads: int = 0
    contacted_leads: int = 0
    replied_leads: int = 0
    failed_leads: int = 0
    pending_jobs: int = 0
