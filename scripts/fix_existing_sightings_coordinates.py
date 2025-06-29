#!/usr/bin/env python3
"""
Fix existing sightings by adding coordinates using the updated LLM validator.
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
from scrapers.llm_validator import LLMValidator
from loguru import logger

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def generate_sql_updates(sightings_with_coords: List[Dict]) -> str:
    """Generate SQL update statements for Supabase."""
    sql_statements = []
    
    sql_statements.append("-- SQL Updates for sighting coordinates")
    sql_statements.append("-- Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sql_statements.append("")
    
    for sighting in sightings_with_coords:
        lat, lng = sighting['coordinates']
        sql = f"""
UPDATE sightings 
SET location = ST_GeomFromText('POINT({lng} {lat})', 4326)
WHERE id = '{sighting['id']}';"""
        sql_statements.append(sql)
    
    sql_statements.append("")
    sql_statements.append(f"-- Total updates: {len(sightings_with_coords)}")
    
    return '\n'.join(sql_statements)

def main():
    """Process all sightings without coordinates."""
    logger.info("Starting coordinate fix for existing sightings...")
    
    # Initialize LLM validator
    validator = LLMValidator()
    
    # Get all sightings without coordinates
    logger.info("Fetching sightings without coordinates...")
    
    all_sightings = []
    offset = 0
    batch_size = 1000
    
    while True:
        response = supabase.table('sightings') \
            .select("*") \
            .is_('location', 'null') \
            .order('created_at', desc=True) \
            .range(offset, offset + batch_size - 1) \
            .execute()
        
        if not response.data:
            break
            
        all_sightings.extend(response.data)
        logger.info(f"Fetched {len(response.data)} sightings (total: {len(all_sightings)})")
        
        if len(response.data) < batch_size:
            break
        offset += batch_size
    
    logger.info(f"Found {len(all_sightings)} sightings without coordinates")
    
    # Process in batches to avoid rate limits
    batch_size = 10
    sightings_with_coords = []
    failed_count = 0
    
    # Limit to first 30 for testing
    all_sightings = all_sightings[:30]
    logger.info(f"LIMITED TO FIRST 30 FOR TESTING")
    
    for i in range(0, len(all_sightings), batch_size):
        batch = all_sightings[i:i + batch_size]
        logger.info(f"\nProcessing batch {i//batch_size + 1}/{(len(all_sightings) + batch_size - 1)//batch_size}")
        
        for sighting in batch:
            location_name = sighting.get('location_name')
            if not location_name or location_name.lower() in ['unknown', 'none', '']:
                continue
            
            # Reconstruct text for LLM analysis
            species = sighting.get('species', 'wildlife')
            description = sighting.get('description', '')
            raw_text = sighting.get('raw_text', '')
            
            # Create context for LLM
            context = f"Wildlife sighting: {species}"
            if location_name:
                context += f" at {location_name}"
            if description:
                context += f". {description}"
            if raw_text and len(raw_text) > len(context):
                context = raw_text[:500]  # Use raw text if more detailed
            
            logger.info(f"  Processing: {location_name}")
            
            try:
                # Use LLM to analyze and extract coordinates
                result = validator.analyze_full_text_for_sighting(
                    context,
                    [species],
                    sighting.get('source_type', 'unknown')
                )
                
                if result and result.get('coordinates'):
                    coords = result['coordinates']
                    logger.success(f"    ✓ Got coordinates: {coords}")
                    
                    sightings_with_coords.append({
                        'id': sighting['id'],
                        'location_name': location_name,
                        'coordinates': coords,
                        'species': species
                    })
                else:
                    logger.warning(f"    ✗ No coordinates extracted")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"    ✗ Error: {e}")
                failed_count += 1
            
            # Rate limiting
            time.sleep(1)
        
        # Longer pause between batches
        if i + batch_size < len(all_sightings):
            logger.info("  Pausing between batches...")
            time.sleep(5)
    
    # Generate results
    logger.info(f"\n{'='*60}")
    logger.info(f"PROCESSING COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total sightings processed: {len(all_sightings)}")
    logger.info(f"Successfully extracted coordinates: {len(sightings_with_coords)}")
    logger.info(f"Failed to extract coordinates: {failed_count}")
    logger.info(f"Skipped (no location name): {len(all_sightings) - len(sightings_with_coords) - failed_count}")
    
    if sightings_with_coords:
        # Save results to JSON
        output_file = f'coordinates_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump(sightings_with_coords, f, indent=2)
        logger.info(f"\nResults saved to: {output_file}")
        
        # Generate SQL file
        sql_file = f'update_coordinates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
        sql_content = generate_sql_updates(sightings_with_coords)
        with open(sql_file, 'w') as f:
            f.write(sql_content)
        logger.info(f"SQL updates saved to: {sql_file}")
        
        # Show sample
        logger.info("\nSample of extracted coordinates:")
        for sighting in sightings_with_coords[:5]:
            logger.info(f"  {sighting['species']} at {sighting['location_name']}: {sighting['coordinates']}")
    
    logger.info("\nNext steps:")
    logger.info("1. Review the generated SQL file")
    logger.info("2. Run it in Supabase SQL editor to update coordinates")
    logger.info("3. The frontend map should then display these sightings")

if __name__ == "__main__":
    main()