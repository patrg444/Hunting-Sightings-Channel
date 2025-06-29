#!/usr/bin/env python3
"""
Fix existing sightings by adding coordinates - batch processing version.
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from loguru import logger

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def process_batch_with_llm(sightings_batch: List[Dict]) -> List[Dict]:
    """Process multiple sightings in one LLM call."""
    
    # Build prompt with all sightings
    prompt = """Extract coordinates for these Colorado wildlife sighting locations. 
For each location, provide the most accurate latitude and longitude you can determine.

Sightings to geocode:
"""
    
    for i, sighting in enumerate(sightings_batch):
        location = sighting.get('location_name', 'Unknown')
        species = sighting.get('species', 'wildlife')
        prompt += f"\n{i+1}. {species} at {location}"
    
    prompt += """

Return a JSON array with coordinates for each sighting:
[
  {"index": 1, "location": "location name", "coordinates": [lat, lon] or null},
  {"index": 2, "location": "location name", "coordinates": [lat, lon] or null},
  ...
]

For known Colorado locations, provide accurate coordinates. Use null if location cannot be determined.
Common Colorado locations:
- Bear Lake, RMNP: [40.3845, -105.6824]
- Estes Park: [40.3775, -105.5253]
- Mount Evans: [39.5883, -105.6438]
- Maroon Bells: [39.0708, -106.9890]
- Quandary Peak: [39.3995, -106.1005]
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a geographic coordinate expert for Colorado locations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in result:
            start = result.find("```json") + 7
            end = result.find("```", start)
            if end > start:
                result = result[start:end].strip()
        elif "```" in result:
            start = result.find("```") + 3
            end = result.find("```", start)
            if end > start:
                result = result[start:end].strip()
        
        # Parse results
        coordinates_data = json.loads(result)
        
        # Map results back to sightings
        results = []
        for item in coordinates_data:
            idx = item['index'] - 1
            if 0 <= idx < len(sightings_batch):
                sighting = sightings_batch[idx]
                if item.get('coordinates') and isinstance(item['coordinates'], list) and len(item['coordinates']) == 2:
                    # Validate coordinates are not None
                    lat, lng = item['coordinates']
                    if lat is not None and lng is not None:
                        results.append({
                            'id': sighting['id'],
                            'location_name': sighting['location_name'],
                            'species': sighting['species'],
                            'coordinates': [lat, lng]
                        })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return []

def generate_sql_updates(sightings_with_coords: List[Dict]) -> str:
    """Generate SQL update statements."""
    sql_statements = []
    
    sql_statements.append("-- Batch coordinate updates for wildlife sightings")
    sql_statements.append("-- Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sql_statements.append("")
    
    for sighting in sightings_with_coords:
        lat, lng = sighting['coordinates']
        sql = f"""UPDATE sightings 
SET location = ST_GeomFromText('POINT({lng} {lat})', 4326)
WHERE id = '{sighting['id']}';"""
        sql_statements.append(sql)
    
    sql_statements.append("")
    sql_statements.append(f"-- Total updates: {len(sightings_with_coords)}")
    
    return '\n'.join(sql_statements)

def main():
    """Process sightings in batches."""
    logger.info("Starting batch coordinate fix for existing sightings...")
    
    # Get all sightings without coordinates
    logger.info("Fetching sightings without coordinates...")
    
    all_sightings = []
    offset = 0
    fetch_batch_size = 1000
    
    while True:
        response = supabase.table('sightings') \
            .select("id,species,location_name,source_type") \
            .is_('location', 'null') \
            .not_.is_('location_name', 'null') \
            .order('created_at', desc=True) \
            .range(offset, offset + fetch_batch_size - 1) \
            .execute()
        
        if not response.data:
            break
            
        # Filter out empty location names
        valid_sightings = [s for s in response.data 
                          if s.get('location_name') and 
                          s['location_name'].lower() not in ['unknown', 'none', '']]
        
        all_sightings.extend(valid_sightings)
        logger.info(f"Fetched {len(valid_sightings)} valid sightings (total: {len(all_sightings)})")
        
        if len(response.data) < fetch_batch_size:
            break
        offset += fetch_batch_size
    
    logger.info(f"Found {len(all_sightings)} sightings to process")
    
    # Process in batches of 5
    batch_size = 5
    all_results = []
    
    # Process all sightings
    logger.info(f"Processing all {len(all_sightings)} sightings")
    
    for i in range(0, len(all_sightings), batch_size):
        batch = all_sightings[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_sightings) + batch_size - 1) // batch_size
        
        logger.info(f"\nProcessing batch {batch_num}/{total_batches}")
        logger.info(f"Locations: {[s['location_name'] for s in batch]}")
        
        # Process batch
        results = process_batch_with_llm(batch)
        
        if results:
            all_results.extend(results)
            logger.success(f"Extracted {len(results)} coordinates from batch")
            for r in results:
                logger.info(f"  ✓ {r['species']} at {r['location_name']}: {r['coordinates']}")
        else:
            logger.warning(f"No coordinates extracted from batch")
        
        # Rate limiting between batches
        if i + batch_size < len(all_sightings):
            time.sleep(2)
    
    # Save results
    logger.info(f"\n{'='*60}")
    logger.info(f"BATCH PROCESSING COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total sightings processed: {len(all_sightings)}")
    logger.info(f"Successfully extracted coordinates: {len(all_results)}")
    logger.info(f"Success rate: {len(all_results)/len(all_sightings)*100:.1f}%")
    
    if all_results:
        # Save JSON results
        output_file = f'batch_coordinates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"\nResults saved to: {output_file}")
        
        # Generate SQL
        sql_file = f'batch_update_coordinates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
        sql_content = generate_sql_updates(all_results)
        with open(sql_file, 'w') as f:
            f.write(sql_content)
        logger.info(f"SQL updates saved to: {sql_file}")
        
        logger.info("\nSample results:")
        for r in all_results[:5]:
            logger.info(f"  {r['species']} at {r['location_name']}: {r['coordinates']}")

if __name__ == "__main__":
    main()