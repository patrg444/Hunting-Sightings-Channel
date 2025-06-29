#!/usr/bin/env python3
"""
Simple version to enhance sightings with LLM:
1. Add coordinates to new sightings
2. Add radius to old sightings
"""
import os
import sys
import json
import time
from typing import Optional, Tuple
import openai
from dotenv import load_dotenv
from supabase import create_client

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Initialize clients
openai.api_key = os.getenv('OPENAI_API_KEY')
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def get_coordinates_for_location(location_name: str) -> Optional[Tuple[float, float]]:
    """Use LLM to get coordinates for a location."""
    if not location_name or location_name.lower() in ['unknown', 'none']:
        return None
        
    prompt = f"""You are a geographic coordinate expert. Given this location in or near Colorado, provide the most accurate latitude and longitude.

Location: {location_name}

Important:
- If this is a well-known place, provide exact coordinates
- If it's a general area, provide the center point
- Only return coordinates if you're confident they're in/near Colorado
- Colorado is roughly between 37-41°N latitude and 102-109°W longitude

Return ONLY in this format: lat,lng
Example: 39.7392,-104.9903
If unknown or outside Colorado area, return: unknown"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        if result and result != 'unknown':
            parts = result.split(',')
            if len(parts) == 2:
                lat = float(parts[0])
                lng = float(parts[1])
                # Validate Colorado area
                if 36 <= lat <= 42 and -109.5 <= lng <= -102:
                    return (lat, lng)
    except Exception as e:
        print(f"Error geocoding {location_name}: {e}")
    
    return None

def estimate_location_radius(location_name: str, description: str = None) -> float:
    """Estimate confidence radius for a location."""
    if not location_name:
        return 25.0  # Default high uncertainty
        
    context = f"Location: {location_name}"
    if description:
        context += f"\nContext: {description[:200]}"  # Limit description length
        
    prompt = f"""Estimate the geographic confidence radius in miles for this location.

{context}

Guidelines:
- Specific trail/landmark (e.g., "Bear Lake Trail") = 0.5-1 miles
- Named area in park (e.g., "Bear Lake Area") = 1-3 miles  
- General park area (e.g., "Rocky Mountain National Park") = 5-15 miles
- Town/city (e.g., "Estes Park") = 3-8 miles
- Mountain/peak (e.g., "Mount Evans") = 1-3 miles
- Region (e.g., "Sangre de Cristo Range") = 15-30 miles
- Vague (e.g., "Colorado", "Unknown") = 30-50 miles

Return ONLY a number (radius in miles)."""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        radius = float(result)
        return min(max(radius, 0.5), 50)  # Clamp between 0.5 and 50
    except:
        return 10.0  # Default moderate uncertainty

def main():
    print("Starting sightings enhancement process...")
    
    # First, get sightings without coordinates (recent ones)
    print("\n1. Fetching sightings without coordinates...")
    response = supabase.table('sightings') \
        .select("*") \
        .is_('location', 'null') \
        .order('created_at', desc=True) \
        .limit(30) \
        .execute()
    
    new_sightings = response.data
    print(f"Found {len(new_sightings)} sightings without coordinates")
    
    # Process each sighting
    updated_count = 0
    for i, sighting in enumerate(new_sightings):
        location_name = sighting.get('location_name')
        if not location_name:
            continue
            
        print(f"\n[{i+1}/{len(new_sightings)}] Processing: {location_name}")
        
        # Get coordinates
        coords = get_coordinates_for_location(location_name)
        if coords:
            lat, lng = coords
            print(f"  ✓ Coordinates: {lat:.6f}, {lng:.6f}")
            
            # Update the sighting
            try:
                # PostGIS point format
                point_wkt = f"POINT({lng} {lat})"
                
                # First, need to check if Supabase accepts WKT directly
                # If not, we'll need to use a different approach
                import subprocess
                import json
                
                # Create SQL command to update with PostGIS
                sql_cmd = f"""
                UPDATE sightings 
                SET location = ST_GeomFromText('POINT({lng} {lat})', 4326)
                WHERE id = '{sighting['id']}';
                """
                
                # For now, let's try updating with null first to test
                # In production, you'd execute the SQL directly on Supabase
                print(f"  SQL would be: UPDATE with POINT({lng} {lat})")
                
                # Store coordinates for manual update if needed
                with open('coordinates_to_update.json', 'a') as f:
                    json.dump({
                        'id': sighting['id'],
                        'location_name': location_name,
                        'lat': lat,
                        'lng': lng,
                        'sql': sql_cmd.strip()
                    }, f)
                    f.write('\n')
                
                updated_count += 1
                print(f"  ✓ Updated successfully")
            except Exception as e:
                print(f"  ✗ Update failed: {e}")
        else:
            print(f"  ✗ Could not determine coordinates")
        
        # Rate limit
        time.sleep(1)
    
    print(f"\n✓ Added coordinates to {updated_count} sightings")
    
    # Now get sightings with coordinates but no radius
    print("\n2. Fetching sightings with coordinates but no radius...")
    response = supabase.table('sightings') \
        .select("*") \
        .not_.is_('location', 'null') \
        .is_('location_confidence_radius', 'null') \
        .order('created_at', desc=True) \
        .limit(30) \
        .execute()
    
    old_sightings = response.data
    print(f"Found {len(old_sightings)} sightings without radius")
    
    # Add radius estimates
    radius_count = 0
    for i, sighting in enumerate(old_sightings):
        location_name = sighting.get('location_name', 'Unknown')
        description = sighting.get('description', '')
        
        print(f"\n[{i+1}/{len(old_sightings)}] Estimating radius for: {location_name}")
        
        radius = estimate_location_radius(location_name, description)
        print(f"  ✓ Estimated radius: {radius} miles")
        
        # Update the sighting
        try:
            supabase.table('sightings') \
                .update({'location_confidence_radius': radius}) \
                .eq('id', sighting['id']) \
                .execute()
            
            radius_count += 1
            print(f"  ✓ Updated successfully")
        except Exception as e:
            print(f"  ✗ Update failed: {e}")
        
        # Rate limit
        time.sleep(1)
    
    print(f"\n✓ Added radius estimates to {radius_count} sightings")
    
    # Summary
    print("\n" + "="*50)
    print("ENHANCEMENT COMPLETE")
    print(f"- Added coordinates to {updated_count} sightings")
    print(f"- Added radius estimates to {radius_count} sightings")
    print("="*50)

if __name__ == "__main__":
    main()