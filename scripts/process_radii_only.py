#!/usr/bin/env python3
"""
Process only the location radii for old sightings.
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

def process_batch_for_radii(sightings_batch: List[Dict]) -> List[Dict]:
    """Process multiple sightings to estimate location confidence radii."""
    
    prompt = """Estimate the geographical confidence radius (in miles) for these wildlife sighting locations based on how specific the location description is.

Sightings to analyze:
"""
    
    for i, sighting in enumerate(sightings_batch):
        location = sighting.get('location_name', '')
        description = sighting.get('description') or ''
        description = description[:100] if description else ''  # First 100 chars
        
        context = f"{i+1}. "
        if location:
            context += f"Location: {location}"
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
- General area only: 20-30 miles
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

def generate_update_sql(updates: List[Dict]) -> str:
    """Generate SQL update statements."""
    sql_lines = [
        f"-- Location radius updates for wildlife sightings",
        f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Total updates: {len(updates)}",
        "",
        "BEGIN;",
        ""
    ]
    
    for update in updates:
        sql_lines.append(
            f"UPDATE sightings "
            f"SET location_confidence_radius = {update['location_confidence_radius']} "
            f"WHERE id = '{update['id']}';"
        )
    
    sql_lines.extend([
        "",
        "COMMIT;",
        "",
        "-- Verification query:",
        "-- SELECT COUNT(*) FROM sightings WHERE location_confidence_radius IS NOT NULL;"
    ])
    
    return '\n'.join(sql_lines)

def main():
    """Process old sightings for location radii."""
    logger.info("Processing sightings for location radii...")
    
    # Get count
    count_response = supabase.table('sightings') \
        .select("id", count='exact') \
        .not_.is_('location', 'null') \
        .is_('location_confidence_radius', 'null') \
        .execute()
    
    total_count = count_response.count
    logger.info(f"Found {total_count} sightings needing location radius")
    
    if total_count == 0:
        logger.info("No sightings need radius updates")
        return
    
    # Fetch all sightings
    all_sightings = []
    offset = 0
    
    while offset < total_count:
        response = supabase.table('sightings') \
            .select("id,location_name,description") \
            .not_.is_('location', 'null') \
            .is_('location_confidence_radius', 'null') \
            .order('created_at', desc=True) \
            .range(offset, min(offset + 999, total_count - 1)) \
            .execute()
        
        all_sightings.extend(response.data)
        logger.info(f"Fetched {len(response.data)} sightings (total: {len(all_sightings)})")
        offset += 1000
    
    logger.info(f"Processing {len(all_sightings)} sightings for location radii...")
    
    # Process in batches
    batch_size = 5
    radius_updates = []
    
    for i in range(0, len(all_sightings), batch_size):
        batch = all_sightings[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_sightings) + batch_size - 1) // batch_size
        
        if batch_num % 10 == 1:
            logger.info(f"Progress: Batch {batch_num}/{total_batches} ({i}/{len(all_sightings)} sightings)")
        
        results = process_batch_for_radii(batch)
        if results:
            radius_updates.extend(results)
            logger.debug(f"Batch {batch_num}: {len(results)} radii estimated")
        
        # Rate limit
        if i + batch_size < len(all_sightings):
            time.sleep(1.5)
    
    # Generate SQL file
    logger.success(f"Estimated radii for {len(radius_updates)} sightings")
    
    if radius_updates:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_file = f'update_radii_{timestamp}.sql'
        
        with open(sql_file, 'w') as f:
            f.write(generate_update_sql(radius_updates))
        
        logger.info(f"\n{'='*60}")
        logger.info("RADIUS PROCESSING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total sightings processed: {len(all_sightings)}")
        logger.info(f"Radius updates generated: {len(radius_updates)}")
        logger.info(f"Success rate: {len(radius_updates)/len(all_sightings)*100:.1f}%")
        logger.info(f"\nSQL file saved to: {sql_file}")
        logger.info("\nNext step: Run the SQL file in Supabase SQL editor")

if __name__ == "__main__":
    main()