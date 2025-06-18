"""Schemas for user management."""

from typing import Optional, List
from datetime import time, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class UserSignUp(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str


class UserSignIn(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: EmailStr
    created_at: Optional[datetime] = None
    email_confirmed_at: Optional[datetime] = None


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences."""
    email_notifications: bool = True
    notification_time: time = time(6, 0)  # 6 AM default
    gmu_filter: List[int] = []  # Empty = all GMUs
    species_filter: List[str] = []  # Empty = all species


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    email_notifications: Optional[bool] = None
    notification_time: Optional[time] = None
    gmu_filter: Optional[List[int]] = None
    species_filter: Optional[List[str]] = None


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
