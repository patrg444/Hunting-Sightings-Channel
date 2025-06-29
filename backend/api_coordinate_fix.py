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
    
    # Convert datetime objects to ISO strings
    for key in ['sighting_date', 'created_at', 'updated_at', 'extracted_at']:
        if key in sighting and sighting[key]:
            if hasattr(sighting[key], 'isoformat'):
                sighting[key] = sighting[key].isoformat()
    
    return sighting

@app.get("/api/v1/sightings")
def get_sightings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = 0,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    species: Optional[str] = None,
    gmu: Optional[int] = None
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
        if species:
            query += " AND species = %s"
            params.append(species)
        if gmu:
            query += " AND gmu_unit = %s"
            params.append(gmu)
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query}) as counted"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add ordering and pagination
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute main query
        cursor.execute(query, params)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Transform results
        sightings = [transform_sighting(row, columns) for row in cursor.fetchall()]
        
        return {
            "sightings": sightings,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total // page_size) + (1 if total % page_size > 0 else 0)
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
        query = """
            SELECT 
                id, species, sighting_date, location_name,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lng,
                location_confidence_radius,
                source_type, description
            FROM sightings
            WHERE location IS NOT NULL
            AND sighting_date >= CURRENT_DATE - INTERVAL '30 days'
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