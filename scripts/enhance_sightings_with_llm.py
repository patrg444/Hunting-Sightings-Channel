#!/usr/bin/env python3
"""
Enhance existing sightings:
1. Add coordinates to new sightings that only have location_name
2. Add location_confidence_radius to old sightings that have coordinates
3. Merge and deduplicate
"""
import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import openai
from dotenv import load_dotenv
from supabase import create_client
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Initialize clients
openai.api_key = os.getenv('OPENAI_API_KEY')
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def extract_coordinates_with_llm(location_name: str) -> Optional[Tuple[float, float]]:
    """Use LLM to extract lat/lng coordinates from location name."""
    if not location_name or location_name.lower() in ['unknown', 'none']:
        return None
        
    prompt = f"""Given this location name in Colorado or nearby areas, provide the latitude and longitude coordinates.
Location: {location_name}

Return ONLY a JSON object with lat and lng fields. If you cannot determine coordinates, return null.
Example: {{"lat": 39.7392, "lng": -104.9903}}
"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        result = response.choices[0].message.content.strip()
        if result and result != 'null':
            coords = json.loads(result)
            if 'lat' in coords and 'lng' in coords:
                # Basic validation for Colorado area
                lat, lng = coords['lat'], coords['lng']
                if 36 <= lat <= 42 and -109.5 <= lng <= -102:
                    return (lat, lng)
    except Exception as e:
        print(f"Error geocoding {location_name}: {e}")
    
    return None

def estimate_radius_with_llm(location_name: str, description: str = None) -> Optional[float]:
    """Use LLM to estimate location confidence radius."""
    if not location_name:
        return None
        
    context = f"Location: {location_name}"
    if description:
        context += f"\nDescription: {description}"
        
    prompt = f"""Estimate the geographic confidence radius in miles for this wildlife sighting location.
{context}

Consider:
- Specific landmarks/trails = 0.5-2 miles radius
- General park areas = 2-5 miles radius  
- Towns/cities = 5-10 miles radius
- Regions/ranges = 10-25 miles radius
- Vague/unknown = 25+ miles radius

Return ONLY a number (the radius in miles).
"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        radius = float(result)
        return min(max(radius, 0.5), 50)  # Clamp between 0.5 and 50 miles
    except Exception as e:
        print(f"Error estimating radius for {location_name}: {e}")
    
    return None

def convert_postgis_to_latlon(geom_str: str) -> Optional[Tuple[float, float]]:
    """Convert PostGIS geometry string to lat/lon tuple."""
    # PostGIS format: 0101000020E6100000<lng_hex><lat_hex>
    # This is a simplified parser - in production use proper PostGIS libraries
    try:
        import struct
        hex_str = geom_str[18:]  # Skip the header
        lng_bytes = bytes.fromhex(hex_str[:16])
        lat_bytes = bytes.fromhex(hex_str[16:32])
        lng = struct.unpack('>d', lng_bytes)[0]
        lat = struct.unpack('>d', lat_bytes)[0]
        return (lat, lng)
    except:
        return None

def enhance_sightings():
    """Main function to enhance all sightings."""
    print("Fetching all sightings from database...")
    
    # Get all sightings
    all_sightings = []
    offset = 0
    batch_size = 1000
    
    while True:
        response = supabase.table('sightings') \
            .select("*") \
            .range(offset, offset + batch_size - 1) \
            .execute()
        
        if not response.data:
            break
            
        all_sightings.extend(response.data)
        if len(response.data) < batch_size:
            break
        offset += batch_size
    
    print(f"Found {len(all_sightings)} total sightings")
    
    # Separate sightings
    new_without_coords = []
    old_without_radius = []
    complete_sightings = []
    
    for s in all_sightings:
        has_coords = s.get('location') is not None
        has_radius = s.get('location_confidence_radius') is not None
        
        if not has_coords and not has_radius:
            new_without_coords.append(s)
        elif has_coords and not has_radius:
            old_without_radius.append(s)
        else:
            complete_sightings.append(s)
    
    print(f"\nSightings breakdown:")
    print(f"- Need coordinates: {len(new_without_coords)}")
    print(f"- Need radius: {len(old_without_radius)}")
    print(f"- Complete: {len(complete_sightings)}")
    
    # Process new sightings - add coordinates
    if new_without_coords:
        print(f"\nProcessing {len(new_without_coords)} sightings without coordinates...")
        enhanced_new = []
        
        for i, sighting in enumerate(new_without_coords[:50]):  # Limit to 50 for now
            location_name = sighting.get('location_name')
            if location_name:
                print(f"  [{i+1}/50] Geocoding: {location_name}")
                coords = extract_coordinates_with_llm(location_name)
                
                if coords:
                    lat, lng = coords
                    # Convert to PostGIS format (simplified)
                    sighting['location'] = f"POINT({lng} {lat})"
                    sighting['_lat'] = lat
                    sighting['_lng'] = lng
                    enhanced_new.append(sighting)
                    print(f"    ✓ Found: {lat:.4f}, {lng:.4f}")
                
                # Rate limit
                time.sleep(0.5)
        
        print(f"Successfully geocoded {len(enhanced_new)} sightings")
    
    # Process old sightings - add radius
    if old_without_radius:
        print(f"\nProcessing {len(old_without_radius)} sightings without radius...")
        enhanced_old = []
        
        for i, sighting in enumerate(old_without_radius[:50]):  # Limit to 50 for now
            location_name = sighting.get('location_name', 'Unknown')
            description = sighting.get('description', '')
            
            print(f"  [{i+1}/50] Estimating radius for: {location_name}")
            radius = estimate_radius_with_llm(location_name, description)
            
            if radius:
                sighting['location_confidence_radius'] = radius
                enhanced_old.append(sighting)
                print(f"    ✓ Radius: {radius} miles")
            
            # Rate limit
            time.sleep(0.5)
        
        print(f"Successfully added radius to {len(enhanced_old)} sightings")
    
    # Update database
    if enhanced_new:
        print(f"\nUpdating {len(enhanced_new)} sightings with coordinates...")
        for sighting in enhanced_new:
            try:
                # Update with raw SQL to handle PostGIS
                lat, lng = sighting['_lat'], sighting['_lng']
                supabase.rpc('update_sighting_location', {
                    'sighting_id': sighting['id'],
                    'lat': lat,
                    'lng': lng
                }).execute()
                print(f"  ✓ Updated {sighting['id']}")
            except Exception as e:
                print(f"  ✗ Failed to update {sighting['id']}: {e}")
    
    if enhanced_old:
        print(f"\nUpdating {len(enhanced_old)} sightings with radius...")
        for sighting in enhanced_old:
            try:
                supabase.table('sightings') \
                    .update({'location_confidence_radius': sighting['location_confidence_radius']}) \
                    .eq('id', sighting['id']) \
                    .execute()
                print(f"  ✓ Updated {sighting['id']}")
            except Exception as e:
                print(f"  ✗ Failed to update {sighting['id']}: {e}")
    
    print("\nEnhancement complete!")
    return enhanced_new, enhanced_old

if __name__ == "__main__":
    enhance_sightings()