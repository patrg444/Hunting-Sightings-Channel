#!/usr/bin/env python3
"""
Monitor data quality of scraped sightings.
"""

import sys
from pathlib import Path
from supabase import create_client
from datetime import datetime, timedelta
import json

sys.path.append(str(Path(__file__).parent.parent))

# Supabase
SUPABASE_URL = 'https://rvrdbtrxwndeerqmziuo.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2cmRidHJ4d25kZWVycW16aXVvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDg0NjU1NywiZXhwIjoyMDY2NDIyNTU3fQ.0cPsbOqpwsuP36akMsRrmkV67pG0uScm2DI5Q7B23Ts'

def main():
    """Monitor data quality."""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Get recent sightings (last 2 hours)
    two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    
    recent = supabase.table('sightings').select('*').gte('created_at', two_hours_ago).order('created_at', desc=True).execute()
    
    print(f"\n=== Recent Sightings (last 2 hours) ===")
    print(f"Total: {len(recent.data)}")
    
    with_coords = 0
    with_gmu = 0
    
    for sighting in recent.data:
        has_coords = sighting.get('location') is not None
        has_gmu = sighting.get('gmu_unit') is not None
        
        if has_coords:
            with_coords += 1
        if has_gmu:
            with_gmu += 1
        
        # Show details for recent ones
        created = datetime.fromisoformat(sighting['created_at'].replace('Z', '+00:00'))
        mins_ago = (datetime.utcnow() - created.replace(tzinfo=None)).total_seconds() / 60
        
        if mins_ago < 30:  # Last 30 minutes
            print(f"\n{sighting['species']} - {int(mins_ago)} mins ago")
            print(f"  Location: {sighting.get('location_name', 'Unknown')}")
            print(f"  Coordinates: {'Yes' if has_coords else 'No'}")
            print(f"  GMU: {sighting.get('gmu_unit') or 'None'}")
            print(f"  Source: {sighting['source_type']}")
            print(f"  Confidence: {sighting.get('confidence_score', 0)}")
    
    print(f"\n=== Quality Metrics ===")
    print(f"With coordinates: {with_coords}/{len(recent.data)} ({with_coords/len(recent.data)*100:.1f}%)" if recent.data else "No recent data")
    print(f"With GMU unit: {with_gmu}/{len(recent.data)} ({with_gmu/len(recent.data)*100:.1f}%)" if recent.data else "No recent data")
    
    # Load scraper progress
    progress_file = Path("data/scraper_progress_fixed.json")
    if progress_file.exists():
        with open(progress_file) as f:
            progress = json.load(f)
        
        print(f"\n=== Scraper Progress ===")
        print(f"Reddit: {progress['reddit']['status']} - {progress['reddit']['sightings_found']} found, {progress['reddit']['sightings_stored']} stored")
        print(f"  Subreddits: {', '.join(progress['reddit']['subreddits_completed'])}")
        print(f"iNaturalist: {progress['inaturalist']['status']}")
        print(f"Google Places: {progress['google_places']['status']}")
        print(f"Last update: {progress['last_update']}")

if __name__ == "__main__":
    main()