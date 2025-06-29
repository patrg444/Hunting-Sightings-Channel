#!/usr/bin/env python3
"""
Test scrapers with 24-hour lookback to verify pipeline functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Import scrapers
from scrapers import RedditScraper, INaturalistScraper

def test_reddit_24hr():
    """Test Reddit scraper with 24-hour lookback."""
    logger.info("\nTesting Reddit Scraper (24-hour lookback)")
    logger.info("="*60)
    
    try:
        scraper = RedditScraper()
        sightings = scraper.scrape(lookback_days=1)  # 1 full day
        
        logger.info(f"Found {len(sightings)} sightings")
        
        if sightings:
            # Show first few sightings
            for i, sighting in enumerate(sightings[:3], 1):
                logger.info(f"\nSighting {i}:")
                logger.info(f"  Species: {sighting.get('species')}")
                logger.info(f"  Location: {sighting.get('location_name')}")
                logger.info(f"  Coordinates: {sighting.get('coordinates')}")
                logger.info(f"  Radius: {sighting.get('location_confidence_radius')} miles")
                logger.info(f"  Date: {sighting.get('sighting_date')}")
                logger.info(f"  Subreddit: {sighting.get('subreddit')}")
            
            # Test saving to database
            logger.info(f"\nSaving {len(sightings)} sightings to Supabase...")
            
            from scrapers.database_saver import save_sightings_to_db
            saved = save_sightings_to_db(sightings, "reddit")
            
            logger.success(f"Saved {saved} sightings to database")
            
            # Verify in database
            verify_recent_saves("reddit", 5)
            
        return sightings
        
    except Exception as e:
        logger.error(f"Reddit test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def test_inaturalist_24hr():
    """Test iNaturalist scraper with 24-hour lookback."""
    logger.info("\nTesting iNaturalist Scraper (24-hour lookback)")
    logger.info("="*60)
    
    try:
        scraper = INaturalistScraper()
        sightings = scraper.scrape(lookback_days=1)
        
        logger.info(f"Found {len(sightings)} sightings")
        
        if sightings:
            # Show first few
            for i, sighting in enumerate(sightings[:3], 1):
                logger.info(f"\nSighting {i}:")
                logger.info(f"  Species: {sighting.get('species')}")
                logger.info(f"  Location: {sighting.get('location_name')}")
                logger.info(f"  Coordinates: {sighting.get('coordinates')}")
                logger.info(f"  Date: {sighting.get('sighting_date')}")
            
            # Test saving
            logger.info(f"\nSaving {len(sightings)} sightings to Supabase...")
            
            from scrapers.database_saver import save_sightings_to_db
            saved = save_sightings_to_db(sightings, "inaturalist")
            
            logger.success(f"Saved {saved} sightings to database")
            
            # Verify
            verify_recent_saves("inaturalist", 5)
            
        return sightings
        
    except Exception as e:
        logger.error(f"iNaturalist test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def verify_recent_saves(source_type, limit=5):
    """Verify recent saves in database."""
    try:
        conn = psycopg2.connect(
            "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                species,
                location_name,
                sighting_date,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lng,
                location_confidence_radius,
                created_at
            FROM sightings
            WHERE source_type = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (source_type, limit))
        
        recent = cursor.fetchall()
        
        if recent:
            logger.info(f"\nVerified recent {source_type} saves in database:")
            for species, location, date, lat, lng, radius, created in recent:
                coords = f"({lat:.4f}, {lng:.4f})" if lat and lng else "No coords"
                radius_str = f"{radius:.1f} mi" if radius else "No radius"
                logger.info(f"  {species} at {location} on {date} - {coords} - {radius_str}")
        else:
            logger.warning(f"No recent {source_type} entries found in database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")

def main():
    """Run 24-hour pipeline test."""
    logger.info("24-HOUR SCRAPER PIPELINE TEST")
    logger.info(f"Started at: {datetime.now()}")
    
    # Test Reddit
    reddit_sightings = test_reddit_24hr()
    
    # Test iNaturalist
    inat_sightings = test_inaturalist_24hr()
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Reddit: {len(reddit_sightings)} sightings")
    logger.info(f"iNaturalist: {len(inat_sightings)} sightings")
    logger.info(f"Total: {len(reddit_sightings) + len(inat_sightings)} sightings")
    
    # Check database totals
    try:
        conn = psycopg2.connect(
            "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                source_type,
                COUNT(*) as total,
                COUNT(location) as with_coords,
                COUNT(location_confidence_radius) as with_radius
            FROM sightings
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            GROUP BY source_type
        """)
        
        logger.info("\nRecent database activity (last hour):")
        for source, total, coords, radius in cursor.fetchall():
            logger.info(f"  {source}: {total} saved ({coords} with coords, {radius} with radius)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Database summary failed: {e}")
    
    logger.info(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main()