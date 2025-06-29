"""
Updated API endpoint that properly converts PostGIS coordinates for frontend consumption.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import json

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

def transform_sighting(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """Transform database row to frontend-compatible format."""
    sighting = dict(zip(columns, row))
    
    # Convert location if present
    if sighting.get('lat') and sighting.get('lng'):
        sighting['location'] = {
            'lat': sighting['lat'],
            'lon': sighting['lng']  # Frontend expects 'lon' not 'lng'
        }
        # Remove the separate lat/lng fields
        del sighting['lat']
        del sighting['lng']
    else:
        # Set location to None if no coordinates
        sighting['location'] = None
    
    # Convert datetime objects to ISO strings
    for key in ['sighting_date', 'created_at', 'updated_at', 'extracted_at']:
        if key in sighting and sighting[key]:
            if hasattr(sighting[key], 'isoformat'):
                sighting[key] = sighting[key].isoformat()
    
    return sighting

@app.get("/api/v1/sightings")
def get_sightings(
    limit: int = Query(20, ge=1, le=500),
    offset: int = 0,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    species: Optional[str] = None,
    species_list: Optional[str] = None,  # Comma-separated list of species
    gmu: Optional[int] = None,
    gmu_list: Optional[str] = None,  # Comma-separated list of GMUs
    source: Optional[str] = None,
    source_list: Optional[str] = None,  # Comma-separated list of sources
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_miles: Optional[float] = None
):
    """Get sightings with proper coordinate transformation."""
    
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    try:
        # Build the query with coordinate extraction
        query = """
            SELECT 
                id, species, sighting_date, location_name, gmu_unit,
                source_type, source_url, description, confidence_score,
                created_at, updated_at, user_id, validated, raw_text,
                extracted_at, location_accuracy_miles, location_confidence_radius,
                content_hash,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lng
            FROM sightings
            WHERE 1=1
        """
        
        params = []
        
        # Add filters
        if start_date:
            query += " AND sighting_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND sighting_date <= %s"
            params.append(end_date)
            
        # Species filter
        if species_list:
            # Handle comma-separated species list
            species_items = [s.strip().lower() for s in species_list.split(',') if s.strip()]
            if species_items:
                placeholders = ','.join(['%s'] * len(species_items))
                query += f" AND LOWER(species) IN ({placeholders})"
                params.extend(species_items)
        elif species:
            query += " AND LOWER(species) = LOWER(%s)"
            params.append(species)
            
        # GMU filter
        if gmu_list:
            # Handle comma-separated GMU list
            gmu_numbers = [int(g.strip()) for g in gmu_list.split(',') if g.strip().isdigit()]
            if gmu_numbers:
                placeholders = ','.join(['%s'] * len(gmu_numbers))
                query += f" AND gmu_unit IN ({placeholders})"
                params.extend(gmu_numbers)
        elif gmu:
            query += " AND gmu_unit = %s"
            params.append(gmu)
            
        # Source filter
        if source_list:
            # Handle comma-separated source list
            source_items = [s.strip().lower() for s in source_list.split(',') if s.strip()]
            if source_items:
                placeholders = ','.join(['%s'] * len(source_items))
                query += f" AND LOWER(source_type) IN ({placeholders})"
                params.extend(source_items)
        elif source:
            query += " AND LOWER(source_type) = LOWER(%s)"
            params.append(source)
        
        # Add location-based filtering
        if lat and lon and radius_miles:
            # Convert miles to meters (approximately)
            radius_meters = radius_miles * 1609.34
            query += """
                AND ST_DWithin(
                    location::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s
                )
            """
            params.extend([lon, lat, radius_meters])
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as counted"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add ordering and pagination
        # Calculate actual offset based on page
        actual_offset = (page - 1) * page_size
        query += " ORDER BY sighting_date DESC, created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, actual_offset])
        
        # Execute main query
        cursor.execute(query, params)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Transform results
        sightings = [transform_sighting(row, columns) for row in cursor.fetchall()]
        
        # Calculate actual offset based on page
        actual_offset = (page - 1) * page_size
        
        return {
            "items": sightings,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        return {"error": str(e), "sightings": [], "total": 0}
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/sightings/with-coords")
def get_sightings_with_coordinates():
    """Get only sightings that have coordinates for map display."""
    
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    try:
        # Get sightings with coordinates from the last 30 days
        # Exclude default Colorado center coordinates (39.5501, -105.7821)
        query = """
            SELECT 
                id, species, sighting_date, location_name,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lng,
                location_confidence_radius,
                source_type, source_url, description, gmu_unit
            FROM sightings
            WHERE location IS NOT NULL
            AND sighting_date >= CURRENT_DATE - INTERVAL '30 days'
            AND NOT (
                ABS(ST_Y(location::geometry) - 39.5501) < 0.0001 
                AND ABS(ST_X(location::geometry) - (-105.7821)) < 0.0001
            )
            ORDER BY sighting_date DESC
            LIMIT 500
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        
        sightings = []
        for row in cursor.fetchall():
            sighting = dict(zip(columns, row))
            # Transform for frontend
            sighting['location'] = {
                'lat': sighting['lat'],
                'lon': sighting['lng']
            }
            del sighting['lat']
            del sighting['lng']
            
            # Convert date
            if sighting['sighting_date']:
                sighting['sighting_date'] = sighting['sighting_date'].isoformat()
            
            sightings.append(sighting)
        
        return {
            "sightings": sightings,
            "total": len(sightings)
        }
        
    except Exception as e:
        return {"error": str(e), "sightings": [], "total": 0}
    finally:
        cursor.close()
        conn.close()

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "coordinates_enabled": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)