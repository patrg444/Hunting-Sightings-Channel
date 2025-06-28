#!/usr/bin/env python3
"""
Test the updated Google Places scraper to ensure it returns data in the correct format.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from scrapers.google_places_scraper import GooglePlacesScraper
import json

def test_scraper():
    """Test the updated Google Places scraper."""
    
    logger.info("Testing updated Google Places scraper...")
    
    try:
        # Clear a few entries from cache to allow testing
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete a few entries to allow fresh processing
        cursor.execute("""
            DELETE FROM google_review_cache 
            WHERE review_id IN (
                SELECT review_id FROM google_review_cache 
                WHERE has_wildlife_mention = 1 
                LIMIT 2
            )
        """)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {deleted} entries from cache for testing")
        
        # Initialize and run scraper
        scraper = GooglePlacesScraper()
        
        # Get original method and limit to 5 locations
        original_method = scraper._get_colorado_trailhead_places
        scraper._get_colorado_trailhead_places = lambda: original_method()[:5]
        
        sightings = scraper.scrape()
        
        if sightings:
            logger.success(f"Found {len(sightings)} sightings!")
            
            # Check the format of the first sighting
            sighting = sightings[0]
            logger.info("\nFirst sighting format check:")
            
            # Required fields from Reddit/14ers format
            required_fields = [
                'species', 'raw_text', 'keyword_matched', 'source_url', 
                'source_type', 'extracted_at', 'trail_name', 'sighting_date'
            ]
            
            # Additional fields we expect
            expected_fields = [
                'confidence', 'llm_validated', 'location_confidence_radius',
                'latitude', 'longitude', 'place_id', 'place_name'
            ]
            
            logger.info("Required fields:")
            for field in required_fields:
                if field in sighting:
                    logger.success(f"  ✓ {field}: {type(sighting[field]).__name__}")
                else:
                    logger.error(f"  ✗ {field}: MISSING")
            
            logger.info("\nAdditional fields:")
            for field in expected_fields:
                if field in sighting:
                    logger.info(f"  ✓ {field}: {sighting[field]}")
                else:
                    logger.warning(f"  - {field}: Not present")
            
            # Print full sighting for inspection
            logger.info("\nFull sighting data:")
            print(json.dumps(sighting, indent=2, default=str))
            
        else:
            logger.warning("No sightings found - this may be normal if all reviews are cached")
            logger.info("Try running with --clear-cache to test with fresh data")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper()