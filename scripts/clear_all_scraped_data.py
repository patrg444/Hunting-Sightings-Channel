#!/usr/bin/env python3
"""
Clear all existing scraped data to prepare for fresh scraping with new LLM format.
"""

import sqlite3
from pathlib import Path
from loguru import logger
import sys

def clear_all_data():
    """Clear all scraped data from the database."""
    
    db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
    
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return False
    
    # Confirm action
    logger.warning("This will DELETE ALL scraped wildlife sightings data!")
    logger.warning("Tables to be cleared:")
    logger.warning("- wildlife_sightings (all sightings)")
    logger.warning("- google_review_cache (processed review tracking)")
    logger.warning("- google_reviews_raw (raw Google data)")
    logger.warning("- wildlife_events (legacy table)")
    
    response = input("\nAre you sure you want to clear all data? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Operation cancelled")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get counts before clearing
        tables = {
            'wildlife_sightings': 'SELECT COUNT(*) FROM wildlife_sightings',
            'google_review_cache': 'SELECT COUNT(*) FROM google_review_cache',
            'google_reviews_raw': 'SELECT COUNT(*) FROM google_reviews_raw',
            'wildlife_events': 'SELECT COUNT(*) FROM wildlife_events'
        }
        
        logger.info("\nCurrent data counts:")
        for table, query in tables.items():
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                logger.info(f"  {table}: {count} records")
            except sqlite3.OperationalError:
                logger.warning(f"  {table}: Table not found")
        
        # Clear all tables
        logger.info("\nClearing data...")
        
        # Clear wildlife_sightings
        cursor.execute("DELETE FROM wildlife_sightings")
        wildlife_cleared = cursor.rowcount
        logger.success(f"✓ Cleared {wildlife_cleared} records from wildlife_sightings")
        
        # Clear Google review cache
        cursor.execute("DELETE FROM google_review_cache")
        cache_cleared = cursor.rowcount
        logger.success(f"✓ Cleared {cache_cleared} records from google_review_cache")
        
        # Clear raw Google reviews
        cursor.execute("DELETE FROM google_reviews_raw")
        raw_cleared = cursor.rowcount
        logger.success(f"✓ Cleared {raw_cleared} records from google_reviews_raw")
        
        # Clear wildlife_events (legacy)
        cursor.execute("DELETE FROM wildlife_events")
        events_cleared = cursor.rowcount
        logger.success(f"✓ Cleared {events_cleared} records from wildlife_events")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('wildlife_sightings', 'wildlife_events')")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.success("\nAll data cleared successfully!")
        
        # Also clear JSON files
        logger.info("\nClearing JSON sighting files...")
        sightings_dir = Path(__file__).parent.parent / "data" / "sightings"
        if sightings_dir.exists():
            json_files = list(sightings_dir.glob("*.json"))
            for file in json_files:
                if file.name not in ['inaturalist_enriched_with_gmu.json', 'inaturalist_sample.json']:
                    file.unlink()
                    logger.info(f"  Deleted: {file.name}")
        
        logger.success("\nDatabase is now clean and ready for fresh scraping!")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if clear_all_data():
        logger.info("\nNext steps:")
        logger.info("1. Run fresh_scrape_all.py to collect new data with updated LLM")
        logger.info("2. All data will include location_confidence_radius")
        logger.info("3. All validation will use GPT-4.1 nano")
    else:
        sys.exit(1)