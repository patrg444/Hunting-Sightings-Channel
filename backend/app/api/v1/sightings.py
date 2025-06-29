"""Sightings API endpoints."""

from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from geoalchemy2.functions import ST_MakePoint, ST_Distance

from app.database import get_db
from app.models.sighting import Sighting
from app.schemas.sighting import (
    SightingResponse,
    SightingListResponse,
    SightingStats
)
from app.auth.dependencies import get_current_user_optional
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=SightingListResponse)
async def get_sightings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional),
    gmu: Optional[int] = Query(None, description="Filter by GMU unit"),
    species: Optional[str] = Query(None, description="Filter by species"),
    source: Optional[str] = Query(None, description="Filter by source type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    lat: Optional[float] = Query(None, description="User latitude for distance calculation"),
    lon: Optional[float] = Query(None, description="User longitude for distance calculation"),
    radius_miles: Optional[float] = Query(None, description="Filter within radius (miles)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size)
):
    """
    Get paginated list of wildlife sightings with optional filters.
    """
    # Build query
    query = select(Sighting)
    
    # Apply filters
    filters = []
    if gmu:
        filters.append(Sighting.gmu_unit == gmu)
    if species:
        filters.append(Sighting.species.ilike(f"%{species.lower()}%"))
    if source:
        filters.append(Sighting.source_type == source)
    if start_date:
        filters.append(Sighting.sighting_date >= start_date)
    if end_date:
        filters.append(Sighting.sighting_date <= end_date)
    
    # Apply spatial filter if coordinates provided
    if lat and lon and radius_miles:
        # Convert miles to meters (approximately)
        radius_meters = radius_miles * 1609.34
        user_point = ST_MakePoint(lon, lat)
        filters.append(
            ST_Distance(Sighting.location, user_point) <= radius_meters
        )
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.order_by(Sighting.sighting_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    sightings = result.scalars().all()
    
    # Calculate distances if user location provided
    items = []
    for sighting in sightings:
        sighting_dict = {
            "id": sighting.id,
            "species": sighting.species,
            "raw_text": sighting.raw_text,
            "keyword_matched": sighting.keyword_matched,
            "source_url": sighting.source_url,
            "source_type": sighting.source_type,
            "trail_name": sighting.trail_name,
            "gmu_unit": sighting.gmu_unit,
            "confidence_score": sighting.confidence_score,
            "reddit_post_title": sighting.reddit_post_title,
            "subreddit": sighting.subreddit,
            "extracted_at": sighting.extracted_at,
            "sighting_date": sighting.sighting_date,
            "created_at": sighting.created_at,
        }
        
        # Add location data if available
        if sighting.location:
            # Extract coordinates from PostGIS geometry
            # This would need proper implementation based on how location is stored
            sighting_dict["location_lat"] = None  # Extract from geometry
            sighting_dict["location_lon"] = None  # Extract from geometry
            
            # Calculate distance if user location provided
            if lat and lon:
                # This would need proper distance calculation
                sighting_dict["distance_miles"] = None
        
        items.append(SightingResponse(**sighting_dict))
    
    # Calculate total pages
    pages = (total + page_size - 1) // page_size
    
    return SightingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/stats", response_model=SightingStats)
async def get_sighting_stats(
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, description="Number of days to include in stats")
):
    """
    Get statistics about wildlife sightings.
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get total sightings count
    total_query = select(func.count()).select_from(Sighting).where(
        Sighting.sighting_date >= start_date
    )
    total_sightings = await db.scalar(total_query)
    
    # Get species counts
    species_query = (
        select(Sighting.species, func.count().label("count"))
        .where(Sighting.sighting_date >= start_date)
        .group_by(Sighting.species)
        .order_by(func.count().desc())
    )
    species_result = await db.execute(species_query)
    species_counts = {row.species: row.count for row in species_result}
    
    # Get GMU counts
    gmu_query = (
        select(Sighting.gmu_unit, func.count().label("count"))
        .where(
            and_(
                Sighting.sighting_date >= start_date,
                Sighting.gmu_unit.isnot(None)
            )
        )
        .group_by(Sighting.gmu_unit)
        .order_by(func.count().desc())
    )
    gmu_result = await db.execute(gmu_query)
    gmu_counts = {str(row.gmu_unit): row.count for row in gmu_result}
    
    # Get source counts
    source_query = (
        select(Sighting.source_type, func.count().label("count"))
        .where(Sighting.sighting_date >= start_date)
        .group_by(Sighting.source_type)
        .order_by(func.count().desc())
    )
    source_result = await db.execute(source_query)
    source_counts = {row.source_type: row.count for row in source_result}
    
    # Get date range
    date_range_query = select(
        func.min(Sighting.sighting_date).label("min_date"),
        func.max(Sighting.sighting_date).label("max_date")
    ).where(Sighting.sighting_date >= start_date)
    date_result = await db.execute(date_range_query)
    date_row = date_result.first()
    
    return SightingStats(
        total_sightings=total_sightings or 0,
        species_counts=species_counts,
        gmu_counts=gmu_counts,
        source_counts=source_counts,
        date_range={
            "start": date_row.min_date if date_row else None,
            "end": date_row.max_date if date_row else None
        }
    )


@router.get("/{sighting_id}", response_model=SightingResponse)
async def get_sighting(
    sighting_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific sighting by ID.
    """
    query = select(Sighting).where(Sighting.id == sighting_id)
    result = await db.execute(query)
    sighting = result.scalar_one_or_none()
    
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")
    
    return SightingResponse.model_validate(sighting)
