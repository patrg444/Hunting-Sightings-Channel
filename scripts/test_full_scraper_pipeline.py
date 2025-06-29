#!/usr/bin/env python3
"""
Test the full scraper pipeline end-to-end with Supabase integration.
Tests with a small lookback period to verify everything works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import scrapers
from scrapers import (
    RedditScraper,
    INaturalistScraper,
    FourteenersRealScraper,
    GooglePlacesScraper
)

# Import database connection
import psycopg2
from supabase import create_client

def test_supabase_connection():
    """Test Supabase connection."""
    logger.info("Testing Supabase connection...")
    
    try:
        # Test with psycopg2
        conn = psycopg2.connect(
            "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sightings")
        count = cursor.fetchone()[0]
        logger.success(f"✓ PostgreSQL connection successful. Current sightings: {count}")
        cursor.close()
        conn.close()
        
        # Test with Supabase client
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        response = supabase.table('sightings').select("id").limit(1).execute()
        logger.success("✓ Supabase client connection successful")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_scraper(scraper_class, name, lookback_hours=1):
    """Test a single scraper with minimal lookback."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {name} Scraper")
    logger.info(f"{'='*60}")
    
    try:
        # Initialize scraper
        scraper = scraper_class()
        logger.info(f"✓ {name} scraper initialized")
        
        # Convert hours to days (fractional)
        lookback_days = lookback_hours / 24.0
        
        # Run scraper with minimal lookback
        logger.info(f"Scraping with {lookback_hours} hour lookback...")
        sightings = scraper.scrape(lookback_days=lookback_days)
        
        logger.info(f"✓ Found {len(sightings)} sightings")
        
        # Show sample sighting
        if sightings:
            sample = sightings[0]
            logger.info("\nSample sighting:")
            logger.info(f"  Species: {sample.get('species')}")
            logger.info(f"  Location: {sample.get('location_name')}")
            logger.info(f"  Date: {sample.get('sighting_date')}")
            logger.info(f"  Coordinates: {sample.get('coordinates')}")
            logger.info(f"  Radius: {sample.get('location_confidence_radius')}")
            logger.info(f"  Confidence: {sample.get('confidence_score')}")
        
        return sightings
        
    except Exception as e:
        logger.error(f"✗ {name} scraper failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def test_database_save(sightings, source_name):
    """Test saving sightings to database."""
    if not sightings:
        logger.info("No sightings to save")
        return 0
    
    logger.info(f"\nTesting database save for {len(sightings)} sightings...")
    
    try:
        from scrapers.database_saver import save_sightings_to_db
        
        # Save to database
        saved_count = save_sightings_to_db(sightings, source_name)
        
        logger.success(f"✓ Saved {saved_count} sightings to Supabase")
        
        # Verify in database
        conn = psycopg2.connect(
            "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
        )
        cursor = conn.cursor()
        
        # Check recent entries
        cursor.execute("""
            SELECT species, location_name, source_type, created_at
            FROM sightings
            WHERE source_type = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (source_name,))
        
        recent = cursor.fetchall()
        if recent:
            logger.info(f"\nRecent {source_name} entries in database:")
            for species, location, source, created in recent:
                logger.info(f"  {species} at {location} - {created}")
        
        cursor.close()
        conn.close()
        
        return saved_count
        
    except Exception as e:
        logger.error(f"✗ Database save failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def main():
    """Run full pipeline test."""
    logger.info("FULL SCRAPER PIPELINE TEST")
    logger.info(f"Started at: {datetime.now()}")
    
    # Test database connection first
    if not test_supabase_connection():
        logger.error("Database connection failed. Exiting.")
        return
    
    # Test each scraper with very short lookback (1 hour)
    scrapers = [
        (RedditScraper, "Reddit"),
        (INaturalistScraper, "iNaturalist"),
        (FourteenersRealScraper, "14ers"),
        (GooglePlacesScraper, "Google Places")
    ]
    
    total_found = 0
    total_saved = 0
    
    for scraper_class, name in scrapers:
        # Test scraper
        sightings = test_scraper(scraper_class, name, lookback_hours=1)
        total_found += len(sightings)
        
        # Test database save
        if sightings:
            saved = test_database_save(sightings, name.lower().replace(" ", "_"))
            total_saved += saved
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total sightings found: {total_found}")
    logger.info(f"Total sightings saved: {total_saved}")
    logger.info(f"Database save rate: {total_saved/total_found*100:.1f}%" if total_found > 0 else "N/A")
    
    # Check final database state
    conn = psycopg2.connect(
        "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            source_type,
            COUNT(*) as count,
            MAX(created_at) as latest
        FROM sightings
        GROUP BY source_type
        ORDER BY count DESC
    """)
    
    logger.info("\nDatabase summary by source:")
    for source, count, latest in cursor.fetchall():
        logger.info(f"  {source}: {count} total, latest: {latest}")
    
    cursor.close()
    conn.close()
    
    logger.info(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main()