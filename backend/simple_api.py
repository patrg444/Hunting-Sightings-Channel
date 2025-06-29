from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

@app.get("/")
def read_root():
    return {"message": "Wildlife Sightings API"}

@app.get("/api/v1/sightings")
def get_sightings(
    limit: int = 20, 
    offset: int = 0,
    page: int = 1,
    page_size: int = 20,
    start_date: str = None,
    end_date: str = None,
    species: str = None,
    gmu: int = None
):
    try:
        # Use page_size as limit if provided
        if page_size != 20:  # Non-default page_size
            limit = page_size
        
        # Calculate offset from page
        if page > 1:
            offset = (page - 1) * limit
            
        # Build query
        query = supabase.table('sightings').select("*", count='exact')
        
        # Apply filters
        if start_date:
            query = query.gte('sighting_date', start_date)
        if end_date:
            query = query.lte('sighting_date', end_date)
        if species:
            query = query.ilike('species', f'%{species}%')
        if gmu:
            query = query.eq('gmu_unit', gmu)
            
        # Execute with pagination
        response = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Transform to expected format
        return {
            "sightings": response.data,
            "total": response.count if hasattr(response, 'count') else len(response.data),
            "page": page,
            "pageSize": page_size,
            "totalPages": (response.count // page_size) + 1 if hasattr(response, 'count') else 1
        }
    except Exception as e:
        return {"error": str(e), "sightings": [], "total": 0}

@app.get("/api/v1/sightings/count")
def get_count():
    try:
        response = supabase.table('sightings').select("*", count='exact').execute()
        return {"count": response.count}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/sightings/stats")
def get_stats(days: int = 30):
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sightings in date range
        response = supabase.table('sightings') \
            .select("*") \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        
        # Calculate stats
        species_counts = {}
        source_counts = {}
        
        for sighting in response.data:
            # Count species
            species = sighting.get('species', 'unknown')
            species_counts[species] = species_counts.get(species, 0) + 1
            
            # Count sources
            source = sighting.get('source_type', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_sightings": len(response.data),
            "species_counts": species_counts,
            "source_counts": source_counts,
            "days": days
        }
    except Exception as e:
        return {"error": str(e), "total_sightings": 0, "species_counts": {}, "source_counts": {}}