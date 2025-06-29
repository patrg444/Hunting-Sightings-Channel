#!/usr/bin/env python3
"""
Process only the coordinates for new sightings.
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict
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
                                'location_name': sighting['location_name'],
                                'species': sighting['species'],
                                'coordinates': [lat, lng]
                            })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch coordinate extraction failed: {e}")
        return []

def generate_update_sql(updates: List[Dict]) -> str:
    """Generate SQL update statements."""
    sql_lines = [
        f"-- Coordinate updates for wildlife sightings",
        f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Total updates: {len(updates)}",
        "",
        "BEGIN;",
        ""
    ]
    
    for update in updates:
        lat, lng = update['coordinates']
        sql_lines.append(
            f"UPDATE sightings "
            f"SET location = ST_GeomFromText('POINT({lng} {lat})', 4326) "
            f"WHERE id = '{update['id']}';"
        )
    
    sql_lines.extend([
        "",
        "COMMIT;",
        "",
        "-- Verification query:",
        "-- SELECT COUNT(*) FROM sightings WHERE location IS NOT NULL;"
    ])
    
    return '\n'.join(sql_lines)

def main():
    """Process new sightings for coordinates."""
    logger.info("Processing new sightings for coordinates...")
    
    # Get count
    count_response = supabase.table('sightings') \
        .select("id", count='exact') \
        .is_('location', 'null') \
        .not_.is_('location_name', 'null') \
        .execute()
    
    total_count = count_response.count
    logger.info(f"Found {total_count} sightings needing coordinates")
    
    if total_count == 0:
        logger.info("No sightings need coordinate updates")
        return
    
    # Fetch all sightings
    all_sightings = []
    offset = 0
    
    while offset < total_count:
        response = supabase.table('sightings') \
            .select("id,species,location_name") \
            .is_('location', 'null') \
            .not_.is_('location_name', 'null') \
            .order('created_at', desc=True) \
            .range(offset, min(offset + 999, total_count - 1)) \
            .execute()
        
        valid_sightings = [
            s for s in response.data 
            if s.get('location_name') and 
            s['location_name'].lower() not in ['unknown', 'none', '']
        ]
        
        all_sightings.extend(valid_sightings)
        logger.info(f"Fetched {len(valid_sightings)} valid sightings (total: {len(all_sightings)})")
        offset += 1000
    
    logger.info(f"Processing {len(all_sightings)} sightings for coordinates...")
    
    # Process in batches
    batch_size = 5
    coordinate_updates = []
    start_time = time.time()
    
    for i in range(0, len(all_sightings), batch_size):
        batch = all_sightings[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_sightings) + batch_size - 1) // batch_size
        
        if batch_num % 10 == 1:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(all_sightings) - i) / rate if rate > 0 else 0
            logger.info(f"Progress: Batch {batch_num}/{total_batches} ({i}/{len(all_sightings)}) - ETA: {eta/60:.1f} min")
        
        results = process_batch_for_coordinates(batch)
        if results:
            coordinate_updates.extend(results)
            logger.debug(f"Batch {batch_num}: {len(results)} coordinates extracted")
        
        # Rate limit
        if i + batch_size < len(all_sightings):
            time.sleep(1.5)
    
    # Generate results
    elapsed_total = time.time() - start_time
    logger.success(f"Extracted coordinates for {len(coordinate_updates)} sightings")
    
    if coordinate_updates:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = f'coordinates_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump({
                'processed': len(all_sightings),
                'successful': len(coordinate_updates),
                'timestamp': timestamp,
                'sightings': coordinate_updates
            }, f, indent=2)
        
        # Save SQL
        sql_file = f'update_coordinates_{timestamp}.sql'
        with open(sql_file, 'w') as f:
            f.write(generate_update_sql(coordinate_updates))
        
        logger.info(f"\n{'='*60}")
        logger.info("COORDINATE PROCESSING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total time: {elapsed_total/60:.1f} minutes")
        logger.info(f"Total sightings processed: {len(all_sightings)}")
        logger.info(f"Coordinate updates generated: {len(coordinate_updates)}")
        logger.info(f"Success rate: {len(coordinate_updates)/len(all_sightings)*100:.1f}%")
        logger.info(f"\nFiles created:")
        logger.info(f"  JSON: {json_file}")
        logger.info(f"  SQL: {sql_file}")
        logger.info("\nNext step: Run the SQL file in Supabase SQL editor")

if __name__ == "__main__":
    main()