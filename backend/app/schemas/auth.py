"""Schemas for authentication."""

from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: Optional[dict] = None


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr
    redirect_url: str


class PasswordUpdate(BaseModel):
    """Password update schema."""
    new_password: str
