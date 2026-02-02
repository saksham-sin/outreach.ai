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
    delay_minutes: int = Field(default=0, ge=0)  # Minutes to wait before sending (for steps > 1)

    @staticmethod
    def convert_delay_to_seconds(value: int, unit: str) -> int:
        """
        Convert delay from given unit to seconds.
        
        Args:
            value: Delay value
            unit: 'minutes', 'hours', or 'days'
            
        Returns:
            Delay in seconds
        """
        if unit == "minutes":
            return value * 60
        elif unit == "hours":
            return value * 3600
        elif unit == "days":
            return value * 86400
        else:
            raise ValueError(f"Invalid delay unit: {unit}")
    
    @staticmethod
    def convert_seconds_to_delay(seconds: int, unit: str) -> int:
        """
        Convert seconds to specified delay unit.
        
        Args:
            seconds: Delay in seconds
            unit: 'minutes', 'hours', or 'days'
            
        Returns:
            Delay value in the specified unit
        """
        if unit == "minutes":
            return seconds // 60
        elif unit == "hours":
            return seconds // 3600
        elif unit == "days":
            return seconds // 86400
        else:
            raise ValueError(f"Invalid delay unit: {unit}")
    
    @staticmethod
    def delay_days_to_seconds(days: int) -> int:
        """Convert delay_days to seconds for backward compatibility."""
        return days * 86400
    
    @staticmethod
    def seconds_to_delay_days(seconds: int) -> int:
        """Convert seconds to days for backward compatibility."""
        return seconds // 86400


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
    delay_days: Optional[int] = None
    delay_minutes: Optional[int] = None


class EmailTemplateUpdate(SQLModel):
    """Schema for updating an email template."""
    
    subject: Optional[str] = None
    body: Optional[str] = None
    delay_days: Optional[int] = None
    delay_minutes: Optional[int] = None


class EmailTemplateRead(EmailTemplateBase):
    """Schema for reading an email template."""
    
    id: UUID
    campaign_id: UUID
    created_at: datetime
    updated_at: datetime
