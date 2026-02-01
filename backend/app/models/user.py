"""User model - single user per account."""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from uuid import UUID, uuid4


class UserBase(SQLModel):
    """Base user fields."""
    
    email: str = Field(unique=True, index=True, max_length=255)


class User(UserBase, table=True):
    """User database model."""
    
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class UserCreate(SQLModel):
    """Schema for creating a user."""
    
    email: str


class UserRead(UserBase):
    """Schema for reading a user."""
    
    id: UUID
    created_at: datetime
