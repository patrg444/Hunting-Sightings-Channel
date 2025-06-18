#!/usr/bin/env python3
"""
Cleanup script for Google Reviews data.
Runs daily to:
1. Archive review IDs to cache table
2. Delete raw reviews older than 30 days
3. Maintain compliance with Google's licensing
"""

import os
import sys
import psycopg2
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'hunting_sightings'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )


def cleanup_old_reviews():
    """
    Clean up Google reviews older than 30 days.
    Preserves review IDs in cache table for deduplication.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Call the cleanup function
        cursor.execute("SELECT cleanup_old_google_reviews()")
        deleted_count = cursor.fetchone()[0]
        
        conn.commit()
        logger.info(f"Cleaned up {deleted_count} old Google reviews")
        
        # Get current table sizes for monitoring
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM google_reviews_raw) as raw_reviews,
                (SELECT COUNT(*) FROM google_review_cache) as cached_ids,
                (SELECT COUNT(*) FROM wildlife_events WHERE source = 'google_review') as wildlife_events
        """)
        
        stats = cursor.fetchone()
        logger.info(f"Current stats - Raw reviews: {stats[0]}, Cached IDs: {stats[1]}, Wildlife events: {stats[2]}")
        
        # Optional: vacuum the table to reclaim space
        conn.set_isolation_level(0)  # AUTOCOMMIT
        cursor.execute("VACUUM google_reviews_raw")
        logger.info("Vacuumed google_reviews_raw table")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Cleanup failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def verify_compliance():
    """
    Verify that we're compliant with Google's licensing.
    Ensures no raw reviews older than 30 days exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check for any reviews older than 30 days
        cursor.execute("""
            SELECT COUNT(*), MIN(fetched_at) 
            FROM google_reviews_raw 
            WHERE fetched_at < NOW() - INTERVAL '30 days'
        """)
        
        count, oldest_date = cursor.fetchone()
        
        if count > 0:
            logger.warning(f"Found {count} reviews older than 30 days. Oldest: {oldest_date}")
            return False
        else:
            logger.info("✓ Compliance verified: No raw reviews older than 30 days")
            return True
            
    finally:
        cursor.close()
        conn.close()


def main():
    """Main cleanup process."""
    logger.info("Starting Google Reviews cleanup process")
    
    # Run cleanup
    cleanup_old_reviews()
    
    # Verify compliance
    if verify_compliance():
        logger.info("Cleanup completed successfully - compliant with Google licensing")
    else:
        logger.error("Compliance check failed - manual intervention may be needed")
        sys.exit(1)


if __name__ == "__main__":
    main()
