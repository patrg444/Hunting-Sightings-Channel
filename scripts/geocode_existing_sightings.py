#!/usr/bin/env python3
"""
Script to geocode existing sightings that have location names but no coordinates.
Uses the same LLM validator used during scraping.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from loguru import logger
from scrapers.llm_validator import LLMValidator
import time

# Load environment variables
load_dotenv()

# Database connection
SUPABASE_DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:***REMOVED***@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

def get_sightings_needing_geocoding(limit=100):
    """Get sightings with location names but no coordinates."""
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get sightings with location names but no coordinates
        cur.execute("""
            SELECT id, species, location_name, raw_text, gmu_unit, source_type
            FROM sightings
            WHERE location IS NULL
            AND location_name IS NOT NULL
            AND location_name != ''
            AND location_name != 'Unknown'
            ORDER BY sighting_date DESC
            LIMIT %s
        """, (limit,))
        
        sightings = cur.fetchall()
        logger.info(f"Found {len(sightings)} sightings needing geocoding")
        return sightings
        
    finally:
        cur.close()
        conn.close()

def update_sighting_location(sighting_id, latitude, longitude, confidence_radius):
    """Update a sighting with geocoded location."""
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    
    try:
        # Create PostGIS point
        location = f"POINT({longitude} {latitude})"
        
        cur.execute("""
            UPDATE sightings
            SET location = ST_GeogFromText(%s),
                location_confidence_radius = %s
            WHERE id = %s
        """, (location, confidence_radius, sighting_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Failed to update sighting {sighting_id}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def geocode_sightings(dry_run=False):
    """Geocode existing sightings using LLM validator."""
    
    # Initialize validator
    validator = LLMValidator()
    if not validator.llm_available:
        logger.error("LLM not available. Make sure OPENAI_API_KEY is set.")
        return
    
    # Get sightings to geocode
    sightings = get_sightings_needing_geocoding(limit=500)
    
    geocoded_count = 0
    failed_count = 0
    
    for idx, sighting in enumerate(sightings, 1):
        logger.info(f"Processing {idx}/{len(sightings)} - ID {sighting['id']}: {sighting['location_name']}")
        
        # Prepare text for analysis
        text = f"Wildlife sighting of {sighting['species']} at {sighting['location_name']}."
        if sighting['raw_text']:
            text += f" {sighting['raw_text'][:500]}"
        if sighting['gmu_unit']:
            text += f" GMU {sighting['gmu_unit']}"
        
        # Use the validator to extract location
        try:
            analysis = validator.analyze_full_text_for_sighting(
                text,
                [sighting['species']],
                subreddit=sighting['source_type']
            )
            
            if analysis and analysis.get('coordinates'):
                lat, lon = analysis['coordinates']
                confidence_radius = analysis.get('location_confidence_radius', 10)
                
                logger.success(f"Geocoded {sighting['location_name']} to ({lat}, {lon}) with radius {confidence_radius} miles")
                
                if not dry_run:
                    if update_sighting_location(sighting['id'], lat, lon, confidence_radius):
                        geocoded_count += 1
                    else:
                        failed_count += 1
                else:
                    logger.info("DRY RUN: Would update database")
                    geocoded_count += 1
            else:
                logger.warning(f"Could not geocode {sighting['location_name']}")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing sighting {sighting['id']}: {e}")
            failed_count += 1
        
        # Rate limiting
        time.sleep(1)  # Be nice to the API
    
    logger.info(f"\nGeocoding complete!")
    logger.info(f"Successfully geocoded: {geocoded_count}")
    logger.info(f"Failed: {failed_count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Geocode existing sightings')
    parser.add_argument('--dry-run', action='store_true', help='Test without updating database')
    args = parser.parse_args()
    
    geocode_sightings(dry_run=args.dry_run)