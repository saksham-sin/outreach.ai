"""Lead model - contacts belonging to a campaign."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from uuid import UUID, uuid4

from app.domain.enums import LeadStatus

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.email_job import EmailJob


class LeadBase(SQLModel):
    """Base lead fields."""
    
    email: str = Field(max_length=255, index=True)
    first_name: Optional[str] = Field(default=None, max_length=100)
    company: Optional[str] = Field(default=None, max_length=255)


class Lead(LeadBase, table=True):
    """Lead database model."""
    
    __tablename__ = "leads"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaigns.id", index=True)
    status: LeadStatus = Field(default=LeadStatus.PENDING, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    campaign: "Campaign" = Relationship(back_populates="leads")
    jobs: list["EmailJob"] = Relationship(back_populates="lead")


class LeadCreate(LeadBase):
    """Schema for creating a single lead."""
    pass


class LeadRead(LeadBase):
    """Schema for reading a lead."""
    
    id: UUID
    campaign_id: UUID
    status: LeadStatus
    created_at: datetime
    updated_at: datetime


class LeadImportResult(SQLModel):
    """Result of a CSV import operation."""
    
    total_rows: int
    imported: int
    skipped: int
    errors: list[str]
