"""User model - single user per account."""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Text
from uuid import UUID, uuid4


class UserBase(SQLModel):
    """Base user fields."""
    
    email: str = Field(unique=True, index=True, max_length=255)


class User(UserBase, table=True):
    """User database model."""
    
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    company_name: Optional[str] = Field(default=None, max_length=255)
    job_title: Optional[str] = Field(default=None, max_length=100)
    email_signature: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class UserCreate(SQLModel):
    """Schema for creating a user."""
    
    email: str


class UserRead(UserBase):
    """Schema for reading a user."""
    
    id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email_signature: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(SQLModel):
    """Schema for updating user profile."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email_signature: Optional[str] = None
