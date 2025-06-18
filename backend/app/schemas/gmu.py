"""Schemas for Game Management Units."""

from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict


class GMUBase(BaseModel):
    """Base GMU schema."""
    id: int
    name: str


class GMUResponse(GMUBase):
    """GMU response with geometry."""
    model_config = ConfigDict(from_attributes=True)
    
    bounds: Dict[str, float]  # min_lat, max_lat, min_lon, max_lon
    recent_sightings_count: Optional[int] = 0
    popular_species: Optional[List[str]] = []
