#!/usr/bin/env python3
"""
Upload parsed sightings from cache to Supabase using batch operations.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from supabase import create_client
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase config
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rvrdbtrxwndeerqmziuo.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Configure logging
logger.add("logs/upload_batch_{time}.log", rotation="1 day")

def prepare_sighting_record(sighting):
    """Prepare a single sighting record for insertion."""
    try:
        # Parse sighting date
        sighting_date = sighting.get('sighting_date', datetime.now().isoformat())
        if isinstance(sighting_date, str):
            # Clean up the date string
            sighting_date = sighting_date.replace(' ', 'T').split('.')[0]
            if len(sighting_date) == 10:  # Just date
                sighting_date += 'T00:00:00'
        
        # Extract coordinates
        lat, lon = None, None
        if sighting.get('coordinates') and isinstance(sighting['coordinates'], list) and len(sighting['coordinates']) == 2:
            lat, lon = sighting['coordinates'][0], sighting['coordinates'][1]
        
        # Build record
        data = {
            'species': sighting.get('species', 'Unknown').lower(),
            'location_name': sighting.get('location_description', 'Unknown location'),
            'sighting_date': sighting_date,
            'description': sighting.get('raw_text', '')[:500],  # Limit description length
            'raw_text': sighting.get('raw_text', ''),
            'source_type': sighting.get('source_type', 'reddit'),
            'source_url': sighting.get('source_url', ''),
            'confidence_score': float(sighting.get('confidence', 0.5)),
            'extracted_at': sighting.get('extracted_at', datetime.now().isoformat())
        }
        
        # Add GMU if available
        if sighting.get('gmu_unit'):
            try:
                data['gmu_unit'] = int(sighting['gmu_unit'])
            except (ValueError, TypeError):
                pass
        
        # Add location as PostGIS format if we have coordinates
        if lat and lon and lat != 39.5501 and lon != -105.7821:  # Skip default Colorado center
            data['location'] = f"POINT({float(lon)} {float(lat)})"
            data['location_accuracy_miles'] = 1.0  # Accurate coordinates
        elif sighting.get('gmu_unit'):
            # If we have GMU but generic coordinates, mark as less accurate
            data['location_accuracy_miles'] = 50.0  # GMU center accuracy
        
        return data
    except Exception as e:
        logger.error(f"Error preparing sighting: {e}")
        return None

def upload_sightings():
    """Upload sightings from parsed_posts.json to Supabase using batch operations."""
    
    # Initialize Supabase
    if not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_SERVICE_KEY not found in environment")
        return
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info(f"Connected to Supabase at {SUPABASE_URL}")
    
    # Load parsed posts
    cache_file = Path("data/cache/parsed_posts.json")
    if not cache_file.exists():
        logger.error(f"Cache file not found: {cache_file}")
        return
    
    logger.info(f"Loading parsed posts from {cache_file}")
    with open(cache_file, 'r') as f:
        parsed_posts = json.load(f)
    
    # Extract all sightings with source URLs
    all_sightings = []
    url_to_sighting = {}
    
    for post_id, post_data in parsed_posts.items():
        if post_data.get('has_sightings') and post_data.get('sightings'):
            for sighting in post_data['sightings']:
                if sighting.get('source_url'):
                    url_to_sighting[sighting['source_url']] = sighting
                    all_sightings.append(sighting)
    
    logger.info(f"Found {len(all_sightings)} sightings with URLs")
    
    # Get all existing URLs in one query
    logger.info("Fetching existing sightings...")
    existing_urls = set()
    offset = 0
    limit = 1000
    
    while True:
        result = supabase.table('sightings').select('source_url').range(offset, offset + limit - 1).execute()
        if not result.data:
            break
        existing_urls.update(item['source_url'] for item in result.data if item.get('source_url'))
        offset += limit
        logger.info(f"Fetched {len(existing_urls)} existing URLs...")
    
    logger.info(f"Found {len(existing_urls)} existing sightings in database")
    
    # Filter out existing sightings
    new_sightings = [s for s in all_sightings if s.get('source_url') not in existing_urls]
    logger.info(f"Found {len(new_sightings)} new sightings to upload")
    
    if not new_sightings:
        logger.info("No new sightings to upload")
        return
    
    # Prepare records for batch insert
    records_to_insert = []
    for sighting in new_sightings:
        record = prepare_sighting_record(sighting)
        if record:
            records_to_insert.append(record)
    
    logger.info(f"Prepared {len(records_to_insert)} records for insertion")
    
    # Insert in batches
    batch_size = 500
    uploaded = 0
    errors = 0
    
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        logger.info(f"Uploading batch {i//batch_size + 1} ({i} to {i + len(batch)})")
        
        try:
            result = supabase.table('sightings').insert(batch).execute()
            uploaded += len(batch)
            logger.info(f"Successfully uploaded {len(batch)} records")
        except Exception as e:
            errors += len(batch)
            logger.error(f"Error uploading batch: {e}")
            # Try individual inserts for this batch
            logger.info("Trying individual inserts for failed batch...")
            for record in batch:
                try:
                    supabase.table('sightings').insert(record).execute()
                    uploaded += 1
                    errors -= 1
                except Exception as e2:
                    logger.debug(f"Failed to insert record: {e2}")
    
    logger.info(f"\n=== Upload Complete ===")
    logger.info(f"Total new sightings: {len(new_sightings)}")
    logger.info(f"Uploaded: {uploaded}")
    logger.info(f"Errors: {errors}")
    
    # Get total count in database
    count_result = supabase.table('sightings').select('*', count='exact').execute()
    logger.info(f"Total sightings in database: {count_result.count}")

if __name__ == "__main__":
    upload_sightings()