#!/usr/bin/env python3
"""
Process all sightings to add missing coordinates and location radii.
Uses batch processing with GPT-4.1 nano for efficiency.
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def process_batch_for_coordinates(sightings_batch: List[Dict]) -> List[Dict]:
    """Process multiple sightings to extract coordinates."""
    
    prompt = """You are a Colorado geography expert. Extract precise coordinates for these wildlife sighting locations.

Locations to geocode:
"""
    
    for i, sighting in enumerate(sightings_batch):
        location = sighting.get('location_name', 'Unknown')
        species = sighting.get('species', 'wildlife')
        prompt += f"\n{i+1}. {species} at {location}"
    
    prompt += """

Return a JSON array with coordinates:
[
  {"index": 1, "coordinates": [lat, lon] or null},
  {"index": 2, "coordinates": [lat, lon] or null},
  ...
]

Common Colorado locations:
- Bear Lake RMNP: [40.3845, -105.6824]
- Estes Park: [40.3775, -105.5253]
- Mount Evans: [39.5883, -105.6438]
- Maroon Bells: [39.0708, -106.9890]
- Quandary Peak: [39.3995, -106.1005]
- Trail Ridge Road: [40.3925, -105.6836]
- Grand Lake: [40.252, -105.8233]
- Durango: [37.2753, -107.8801]
- Aspen: [39.1911, -106.8175]
- Vail: [39.6403, -106.3742]

Provide coordinates for any recognizable Colorado location. Use null only if location is completely unknown."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a precise geographic coordinate expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Remove comments from JSON (nano model adds them)
        import re
        result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)
        
        # Extract JSON if in code blocks
        if "```json" in result:
            start = result.find("```json") + 7
            end = result.find("```", start)
            result = result[start:end].strip()
        elif "```" in result:
            start = result.find("```") + 3
            end = result.find("```", start)
            result = result[start:end].strip()
        
        # Parse and validate
        coordinates_data = json.loads(result)
        results = []
        
        for item in coordinates_data:
            idx = item['index'] - 1
            if 0 <= idx < len(sightings_batch):
                coords = item.get('coordinates')
                if coords and isinstance(coords, list) and len(coords) == 2:
                    lat, lng = coords
                    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                        # Verify Colorado bounds
                        if 36 <= lat <= 42 and -109.5 <= lng <= -102:
                            sighting = sightings_batch[idx]
                            results.append({
                                'id': sighting['id'],
                                'coordinates': [lat, lng]
                            })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch coordinate extraction failed: {e}")
        return []

def process_batch_for_radii(sightings_batch: List[Dict]) -> List[Dict]:
    """Process multiple sightings to estimate location confidence radii."""
    
    prompt = """Estimate the geographical confidence radius (in miles) for these wildlife sighting locations based on how specific the location description is.

Sightings to analyze:
"""
    
    for i, sighting in enumerate(sightings_batch):
        location = sighting.get('location_name', '')
        gmu = ''  # No gmu_number in current schema
        description = sighting.get('description') or ''
        description = description[:100] if description else ''  # First 100 chars
        
        context = f"{i+1}. "
        if location:
            context += f"Location: {location}"
        if gmu:
            context += f" (GMU {gmu})"
        if description:
            context += f" - '{description}...'"
        
        prompt += f"\n{context}"
    
    prompt += """

Return a JSON array with radius estimates:
[
  {"index": 1, "radius": number_in_miles},
  {"index": 2, "radius": number_in_miles},
  ...
]

Guidelines for radius estimation:
- Specific location (parking lot, bridge, trail junction): 0.5-1 mile
- Trail or creek name: 2-5 miles
- Peak or lake area: 3-8 miles
- Town or general area: 5-15 miles
- GMU only: 20-40 miles
- Vague description: 30-50 miles"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": "You are an expert at estimating geographical confidence radii. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Remove comments and extract JSON
        import re
        result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)
        
        if "```" in result:
            start = result.find("```") + 3
            if "json" in result[start:start+4]:
                start += 4
            end = result.find("```", start)
            result = result[start:end].strip()
        
        # Parse results
        radii_data = json.loads(result)
        results = []
        
        for item in radii_data:
            idx = item['index'] - 1
            if 0 <= idx < len(sightings_batch):
                radius = item.get('radius')
                if radius and isinstance(radius, (int, float)) and 0 < radius <= 100:
                    sighting = sightings_batch[idx]
                    results.append({
                        'id': sighting['id'],
                        'location_confidence_radius': radius
                    })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch radius estimation failed: {e}")
        return []

def generate_update_sql(updates: List[Dict], update_type: str) -> str:
    """Generate SQL update statements."""
    sql_lines = [
        f"-- {update_type} updates for wildlife sightings",
        f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Total updates: {len(updates)}",
        "",
        "BEGIN;",
        ""
    ]
    
    for update in updates:
        if 'coordinates' in update:
            lat, lng = update['coordinates']
            sql_lines.append(
                f"UPDATE sightings "
                f"SET location = ST_GeomFromText('POINT({lng} {lat})', 4326) "
                f"WHERE id = '{update['id']}';"
            )
        elif 'location_confidence_radius' in update:
            sql_lines.append(
                f"UPDATE sightings "
                f"SET location_confidence_radius = {update['location_confidence_radius']} "
                f"WHERE id = '{update['id']}';"
            )
    
    sql_lines.extend([
        "",
        "COMMIT;",
        "",
        "-- Verification queries:",
        "-- SELECT COUNT(*) FROM sightings WHERE location IS NOT NULL;",
        "-- SELECT COUNT(*) FROM sightings WHERE location_confidence_radius IS NOT NULL;"
    ])
    
    return '\n'.join(sql_lines)

def main():
    """Process all sightings."""
    logger.info("Starting comprehensive sighting processing...")
    
    # 1. Process NEW sightings without coordinates
    logger.info("\n=== PROCESSING NEW SIGHTINGS FOR COORDINATES ===")
    
    # Get count
    count_response = supabase.table('sightings') \
        .select("id", count='exact') \
        .is_('location', 'null') \
        .not_.is_('location_name', 'null') \
        .execute()
    
    new_count = count_response.count
    logger.info(f"Found {new_count} sightings needing coordinates")
    
    if new_count > 0:
        # Fetch all new sightings
        all_new = []
        offset = 0
        
        while offset < new_count:
            response = supabase.table('sightings') \
                .select("id,species,location_name") \
                .is_('location', 'null') \
                .not_.is_('location_name', 'null') \
                .order('created_at', desc=True) \
                .range(offset, min(offset + 999, new_count - 1)) \
                .execute()
            
            valid_sightings = [
                s for s in response.data 
                if s.get('location_name') and 
                s['location_name'].lower() not in ['unknown', 'none', '']
            ]
            
            all_new.extend(valid_sightings)
            offset += 1000
        
        logger.info(f"Processing {len(all_new)} sightings for coordinates...")
        
        # Process in batches
        batch_size = 5
        coordinate_updates = []
        
        for i in range(0, len(all_new), batch_size):
            batch = all_new[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_new) + batch_size - 1) // batch_size
            
            if batch_num % 10 == 1:
                logger.info(f"Progress: Batch {batch_num}/{total_batches}")
            
            results = process_batch_for_coordinates(batch)
            coordinate_updates.extend(results)
            
            # Rate limit
            if i + batch_size < len(all_new):
                time.sleep(1.5)
        
        logger.success(f"Extracted coordinates for {len(coordinate_updates)} sightings")
    
    # 2. Process OLD sightings without radius
    logger.info("\n=== PROCESSING OLD SIGHTINGS FOR LOCATION RADII ===")
    
    # Get count
    count_response = supabase.table('sightings') \
        .select("id", count='exact') \
        .not_.is_('location', 'null') \
        .is_('location_confidence_radius', 'null') \
        .execute()
    
    old_count = count_response.count
    logger.info(f"Found {old_count} sightings needing location radius")
    
    if old_count > 0:
        # Fetch all old sightings
        all_old = []
        offset = 0
        
        while offset < old_count:
            response = supabase.table('sightings') \
                .select("id,location_name,description") \
                .not_.is_('location', 'null') \
                .is_('location_confidence_radius', 'null') \
                .order('created_at', desc=True) \
                .range(offset, min(offset + 999, old_count - 1)) \
                .execute()
            
            all_old.extend(response.data)
            offset += 1000
        
        logger.info(f"Processing {len(all_old)} sightings for location radii...")
        
        # Process in batches
        radius_updates = []
        
        for i in range(0, len(all_old), batch_size):
            batch = all_old[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_old) + batch_size - 1) // batch_size
            
            if batch_num % 10 == 1:
                logger.info(f"Progress: Batch {batch_num}/{total_batches}")
            
            results = process_batch_for_radii(batch)
            radius_updates.extend(results)
            
            # Rate limit
            if i + batch_size < len(all_old):
                time.sleep(1.5)
        
        logger.success(f"Estimated radii for {len(radius_updates)} sightings")
    
    # Generate SQL files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if coordinate_updates:
        sql_file = f'update_coordinates_{timestamp}.sql'
        with open(sql_file, 'w') as f:
            f.write(generate_update_sql(coordinate_updates, "Coordinate"))
        logger.info(f"Coordinate updates saved to: {sql_file}")
    
    if radius_updates:
        sql_file = f'update_radii_{timestamp}.sql'
        with open(sql_file, 'w') as f:
            f.write(generate_update_sql(radius_updates, "Location radius"))
        logger.info(f"Radius updates saved to: {sql_file}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("PROCESSING COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Coordinate updates: {len(coordinate_updates) if 'coordinate_updates' in locals() else 0}")
    logger.info(f"Radius updates: {len(radius_updates) if 'radius_updates' in locals() else 0}")
    logger.info("\nNext steps:")
    logger.info("1. Review the generated SQL files")
    logger.info("2. Run them in Supabase SQL editor")
    logger.info("3. The frontend map should display all sightings with proper location data")

if __name__ == "__main__":
    main()