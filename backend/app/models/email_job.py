"""Email job model - scheduled email work units."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from uuid import UUID, uuid4

from app.domain.enums import JobStatus

if TYPE_CHECKING:
    from app.models.lead import Lead


class EmailJobBase(SQLModel):
    """Base email job fields."""
    
    step_number: int = Field(ge=1, le=3)
    scheduled_at: datetime


class EmailJob(EmailJobBase, table=True):
    """Email job database model - represents scheduled email work."""
    
    __tablename__ = "email_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    campaign_id: UUID = Field(foreign_key="campaigns.id", index=True)
    lead_id: UUID = Field(foreign_key="leads.id", index=True)
    status: JobStatus = Field(default=JobStatus.PENDING, index=True)
    scheduled_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    attempts: int = Field(default=0)
    last_error: Optional[str] = Field(default=None, max_length=1000)
    sent_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    message_id: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    lead: "Lead" = Relationship(back_populates="jobs")


class EmailJobCreate(SQLModel):
    """Schema for creating an email job."""
    
    campaign_id: UUID
    lead_id: UUID
    step_number: int
    scheduled_at: datetime


class EmailJobRead(EmailJobBase):
    """Schema for reading an email job."""
    
    id: UUID
    campaign_id: UUID
    lead_id: UUID
    status: JobStatus
    attempts: int
    last_error: Optional[str]
    sent_at: Optional[datetime]
    message_id: Optional[str]
    created_at: datetime
    updated_at: datetime
