#!/usr/bin/env python3
"""
Upload parsed sightings from cache to Supabase.
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
logger.add("logs/upload_parsed_{time}.log", rotation="1 day")

def upload_sightings():
    """Upload sightings from parsed_posts.json to Supabase."""
    
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
    
    # Extract all sightings
    all_sightings = []
    for post_id, post_data in parsed_posts.items():
        if post_data.get('has_sightings') and post_data.get('sightings'):
            for sighting in post_data['sightings']:
                # Add post ID for tracking
                sighting['post_id'] = post_id
                all_sightings.append(sighting)
    
    logger.info(f"Found {len(all_sightings)} total sightings to upload")
    
    # Upload in batches
    batch_size = 100
    uploaded = 0
    skipped = 0
    errors = 0
    
    for i in range(0, len(all_sightings), batch_size):
        batch = all_sightings[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({i} to {i + len(batch)})")
        
        for sighting in batch:
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
                
                # Check if already exists
                if data['source_url']:
                    existing = supabase.table('sightings').select('id').eq('source_url', data['source_url']).execute()
                    if existing.data:
                        skipped += 1
                        continue
                
                # Insert the sighting
                result = supabase.table('sightings').insert(data).execute()
                uploaded += 1
                
                if uploaded % 10 == 0:
                    logger.info(f"Progress: {uploaded} uploaded, {skipped} skipped, {errors} errors")
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error uploading sighting: {e}")
                logger.debug(f"Sighting data: {json.dumps(sighting, default=str)[:200]}...")
    
    logger.info(f"\n=== Upload Complete ===")
    logger.info(f"Total sightings: {len(all_sightings)}")
    logger.info(f"Uploaded: {uploaded}")
    logger.info(f"Skipped (duplicates): {skipped}")
    logger.info(f"Errors: {errors}")
    
    # Get total count in database
    count_result = supabase.table('sightings').select('*', count='exact').execute()
    logger.info(f"Total sightings in database: {count_result.count}")

if __name__ == "__main__":
    upload_sightings()