"""Pydantic schemas for API validation."""

from app.schemas.sighting import (
    SightingBase,
    SightingCreate,
    SightingResponse,
    SightingListResponse,
    SightingStats
)
from app.schemas.user import (
    UserSignUp,
    UserSignIn,
    UserResponse,
    UserPreferencesBase,
    UserPreferencesUpdate,
    UserPreferencesResponse
)
from app.schemas.gmu import GMUBase, GMUResponse
from app.schemas.auth import Token, PasswordReset

__all__ = [
    # Sighting schemas
    "SightingBase",
    "SightingCreate",
    "SightingResponse",
    "SightingListResponse",
    "SightingStats",
    # User schemas
    "UserSignUp",
    "UserSignIn",
    "UserResponse",
    "UserPreferencesBase",
    "UserPreferencesUpdate",
    "UserPreferencesResponse",
    # GMU schemas
    "GMUBase",
    "GMUResponse",
    # Auth schemas
    "Token",
    "PasswordReset"
]
