"""Campaign tags model - flexible tagging for campaigns."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class CampaignTag(SQLModel, table=True):
    """Campaign tag database model."""
    
    __tablename__ = "campaign_tags"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaigns.id", index=True)
    tag: str = Field(max_length=100, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="tags")


class CampaignTagCreate(SQLModel):
    """Schema for creating a campaign tag."""
    tag: str


class CampaignTagRead(SQLModel):
    """Schema for reading a campaign tag."""
    id: UUID
    tag: str
    created_at: datetime
