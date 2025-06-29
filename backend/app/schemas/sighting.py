"""Schemas for wildlife sightings."""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SightingBase(BaseModel):
    """Base sighting schema."""
    species: str
    raw_text: str
    keyword_matched: Optional[str] = None
    source_url: str
    source_type: str
    trail_name: Optional[str] = None
    gmu_unit: Optional[int] = None
    confidence_score: float = 1.0
    reddit_post_title: Optional[str] = None
    subreddit: Optional[str] = None
    location_confidence_radius: Optional[float] = None


class SightingCreate(SightingBase):
    """Schema for creating a sighting."""
    extracted_at: datetime
    sighting_date: Optional[datetime] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None


class SightingResponse(SightingBase):
    """Schema for sighting response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    extracted_at: datetime
    sighting_date: Optional[datetime] = None
    created_at: datetime
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    distance_miles: Optional[float] = None  # Distance from user's location


class SightingListResponse(BaseModel):
    """Paginated list of sightings."""
    items: List[SightingResponse]
    total: int
    page: int = 1
    page_size: int
    pages: int


class SightingStats(BaseModel):
    """Statistics about sightings."""
    total_sightings: int
    species_counts: dict[str, int]
    gmu_counts: dict[str, int]
    source_counts: dict[str, int]
    date_range: dict[str, Optional[datetime]]
