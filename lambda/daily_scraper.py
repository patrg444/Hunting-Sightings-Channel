"""
AWS Lambda function for daily wildlife sighting scraping.
Runs all scrapers with a 1-day lookback period and saves to Supabase.
"""

import os
import json
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (set in Lambda configuration)
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT')
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')

def generate_content_hash(sighting: Dict[str, Any]) -> str:
    """Generate unique hash for deduplication."""
    content = f"{sighting.get('species', '')}_{sighting.get('sighting_date', '')}_{sighting.get('location_name', '')}_{sighting.get('source_type', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def save_to_supabase(sightings: List[Dict[str, Any]], source_name: str) -> Dict[str, int]:
    """Save sightings to Supabase."""
    
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()
    
    saved_count = 0
    duplicate_count = 0
    
    for sighting in sightings:
        try:
            content_hash = generate_content_hash(sighting)
            
            # Convert sighting date
            sighting_date = sighting.get('sighting_date')
            if isinstance(sighting_date, str):
                try:
                    sighting_date = datetime.fromisoformat(sighting_date.replace('Z', '+00:00'))
                    sighting_date = sighting_date.date()
                except:
                    sighting_date = None
            elif hasattr(sighting_date, 'date'):
                sighting_date = sighting_date.date()
            
            # Create PostGIS point
            location = None
            if sighting.get('latitude') and sighting.get('longitude'):
                location = f"POINT({sighting['longitude']} {sighting['latitude']})"
            
            cursor.execute("""
                INSERT INTO sightings (
                    species, raw_text, source_url, source_type,
                    extracted_at, location_name, sighting_date, gmu_unit, location,
                    confidence_score, location_confidence_radius, content_hash
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, ST_GeogFromText(%s),
                    %s, %s, %s
                )
                ON CONFLICT (content_hash) DO NOTHING
            """, (
                sighting.get('species'),
                sighting.get('raw_text', '')[:500],
                sighting.get('source_url'),
                sighting.get('source_type'),
                sighting.get('extracted_at', datetime.now()),
                sighting.get('location_name'),
                sighting_date,
                sighting.get('gmu'),
                location,
                sighting.get('confidence', 80) / 100.0,
                sighting.get('location_confidence_radius'),
                content_hash
            ))
            
            if cursor.rowcount > 0:
                saved_count += 1
            else:
                duplicate_count += 1
                
        except Exception as e:
            logger.error(f"Error saving sighting: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {'saved': saved_count, 'duplicates': duplicate_count}

def lambda_handler(event, context):
    """
    Lambda handler for daily scraping.
    Uses 1-day lookback for daily runs, unless specified otherwise in event.
    """
    
    # Get lookback days from event or default to 1 for daily runs
    lookback_days = event.get('lookback_days', 1)
    
    logger.info(f"Starting daily scrape with {lookback_days} day lookback")
    
    # Import scrapers (these will be included in deployment package)
    try:
        from scrapers import (
            RedditScraper,
            GooglePlacesScraper,
            FourteenersRealScraper,
            INaturalistScraper
        )
    except ImportError as e:
        logger.error(f"Failed to import scrapers: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to import scrapers'})
        }
    
    results = {
        'start_time': datetime.now().isoformat(),
        'lookback_days': lookback_days,
        'sources': {}
    }
    
    # Run each scraper
    scrapers = [
        ('Reddit', RedditScraper),
        ('Google Places', GooglePlacesScraper),
        ('14ers.com', FourteenersRealScraper),
        ('iNaturalist', INaturalistScraper)
    ]
    
    total_saved = 0
    total_found = 0
    
    for name, scraper_class in scrapers:
        logger.info(f"Running {name} scraper...")
        
        try:
            scraper = scraper_class()
            sightings = scraper.scrape(lookback_days=lookback_days)
            
            # Save to Supabase
            save_result = save_to_supabase(sightings, name)
            
            results['sources'][name] = {
                'found': len(sightings),
                'saved': save_result['saved'],
                'duplicates': save_result['duplicates']
            }
            
            total_found += len(sightings)
            total_saved += save_result['saved']
            
            logger.info(f"{name}: Found {len(sightings)}, Saved {save_result['saved']}")
            
        except Exception as e:
            logger.error(f"Error in {name} scraper: {e}")
            results['sources'][name] = {'error': str(e)}
    
    results['end_time'] = datetime.now().isoformat()
    results['total_found'] = total_found
    results['total_saved'] = total_saved
    
    logger.info(f"Scraping complete. Total found: {total_found}, Total saved: {total_saved}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }