#!/usr/bin/env python3
"""
Simple FastAPI server to serve wildlife sightings from SQLite database.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sqlite3
import os
import uvicorn
from datetime import datetime

app = FastAPI(title="Wildlife Sightings API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000", "http://54.203.54.74", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'hunting_sightings.db')

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/v1/wildlife/wildlife-sightings")
async def get_wildlife_sightings(
    species: Optional[List[str]] = Query(None),
    gmu: Optional[int] = Query(None),
    gmu_list: Optional[str] = Query(None),
    source_types: Optional[List[str]] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(500, le=1000)
):
    """Get wildlife sightings with filters."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM wildlife_sightings WHERE 1=1"
    params = []
    
    # Apply filters
    if species:
        placeholders = ','.join('?' * len(species))
        query += f" AND species IN ({placeholders})"
        params.extend(species)
    
    if gmu:
        query += " AND gmu = ?"
        params.append(gmu)
    elif gmu_list:
        # Handle comma-separated GMU list
        gmu_numbers = [int(g.strip()) for g in gmu_list.split(',') if g.strip().isdigit()]
        if gmu_numbers:
            placeholders = ','.join('?' * len(gmu_numbers))
            query += f" AND gmu IN ({placeholders})"
            params.extend(gmu_numbers)
    
    if source_types:
        placeholders = ','.join('?' * len(source_types))
        query += f" AND source_type IN ({placeholders})"
        params.extend(source_types)
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    # Order and limit
    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    
    # Execute query
    cursor.execute(query, params)
    
    # Convert to list of dicts
    sightings = []
    for row in cursor.fetchall():
        sighting = dict(row)
        # Ensure proper formatting
        if sighting['date']:
            sighting['date'] = sighting['date'].replace('T', ' ').split('.')[0]
        sightings.append(sighting)
    
    conn.close()
    
    return {
        "sightings": sightings,
        "total": len(sightings)
    }

@app.get("/api/v1/wildlife/wildlife-stats")
async def get_wildlife_stats():
    """Get wildlife statistics."""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total sightings
    cursor.execute("SELECT COUNT(*) as count FROM wildlife_sightings")
    stats['total_sightings'] = cursor.fetchone()['count']
    
    # By species
    cursor.execute("""
        SELECT species, COUNT(*) as count 
        FROM wildlife_sightings 
        GROUP BY species 
        ORDER BY count DESC
    """)
    stats['by_species'] = [dict(row) for row in cursor.fetchall()]
    
    # By source
    cursor.execute("""
        SELECT source_type, COUNT(*) as count 
        FROM wildlife_sightings 
        GROUP BY source_type 
        ORDER BY count DESC
    """)
    stats['by_source'] = [dict(row) for row in cursor.fetchall()]
    
    # By GMU
    cursor.execute("""
        SELECT gmu, COUNT(*) as count 
        FROM wildlife_sightings 
        WHERE gmu IS NOT NULL
        GROUP BY gmu 
        ORDER BY count DESC
        LIMIT 10
    """)
    stats['top_gmus'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return stats

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Wildlife Sightings API",
        "endpoints": [
            "/api/v1/wildlife/wildlife-sightings",
            "/api/v1/wildlife/wildlife-stats"
        ]
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

if __name__ == "__main__":
    print(f"Starting server with database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("WARNING: Database file not found!")
    uvicorn.run(app, host="0.0.0.0", port=8000)