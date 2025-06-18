"""User preferences API endpoints."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from gotrue.types import User

from app.database import get_db
from app.models.user import UserPreferences
from app.schemas.user import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserPreferencesBase
)
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/prefs", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's preferences.
    """
    query = select(UserPreferences).where(
        UserPreferences.user_id == UUID(current_user.id)
    )
    result = await db.execute(query)
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences if none exist
        preferences = UserPreferences(
            user_id=UUID(current_user.id),
            **UserPreferencesBase().model_dump()
        )
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    
    return UserPreferencesResponse.model_validate(preferences)


@router.put("/prefs", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's preferences.
    """
    # Get existing preferences
    query = select(UserPreferences).where(
        UserPreferences.user_id == UUID(current_user.id)
    )
    result = await db.execute(query)
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create new preferences with updates
        update_data = preferences_update.model_dump(exclude_unset=True)
        preferences = UserPreferences(
            user_id=UUID(current_user.id),
            **update_data
        )
        db.add(preferences)
    else:
        # Update existing preferences
        update_data = preferences_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
    
    await db.commit()
    await db.refresh(preferences)
    
    return UserPreferencesResponse.model_validate(preferences)


@router.delete("/prefs")
async def reset_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset user preferences to defaults.
    """
    # Get existing preferences
    query = select(UserPreferences).where(
        UserPreferences.user_id == UUID(current_user.id)
    )
    result = await db.execute(query)
    preferences = result.scalar_one_or_none()
    
    if preferences:
        # Reset to defaults
        defaults = UserPreferencesBase()
        for field, value in defaults.model_dump().items():
            setattr(preferences, field, value)
        
        await db.commit()
    
    return {"message": "Preferences reset to defaults"}
