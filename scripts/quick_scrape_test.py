#!/usr/bin/env python3
"""
Quick test to verify full pipeline works with coordinates.
"""

from scrapers.reddit_scraper import RedditScraper
from scrapers.inaturalist_scraper import INaturalistScraper
from loguru import logger
import psycopg2

def main():
    logger.info("Running quick scraping test...")
    
    # Test Reddit scraper
    logger.info("\n=== Testing Reddit Scraper ===")
    reddit = RedditScraper()
    reddit_sightings = reddit.scrape(lookback_days=1)
    logger.info(f"Found {len(reddit_sightings)} Reddit sightings")
    
    # Test iNaturalist scraper
    logger.info("\n=== Testing iNaturalist Scraper ===")
    inat = INaturalistScraper()
    inat_sightings = inat.scrape(days_back=1)
    logger.info(f"Found {len(inat_sightings)} iNaturalist sightings")
    
    # Check database for recent entries with coordinates
    logger.info("\n=== Checking Database ===")
    conn = psycopg2.connect(
        "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(location) as with_coords,
            COUNT(location_confidence_radius) as with_radius
        FROM sightings
        WHERE created_at >= NOW() - INTERVAL '1 hour'
    """)
    
    total, with_coords, with_radius = cursor.fetchone()
    logger.info(f"Recent sightings (last hour):")
    logger.info(f"  Total: {total}")
    logger.info(f"  With coordinates: {with_coords} ({with_coords/total*100:.1f}%)" if total > 0 else "  No recent sightings")
    logger.info(f"  With radius: {with_radius} ({with_radius/total*100:.1f}%)" if total > 0 else "")
    
    # Show a sample
    cursor.execute("""
        SELECT species, location_name, 
               ST_Y(location::geometry) as lat,
               ST_X(location::geometry) as lng,
               location_confidence_radius
        FROM sightings
        WHERE location IS NOT NULL
        AND created_at >= NOW() - INTERVAL '1 hour'
        LIMIT 3
    """)
    
    logger.info("\nSample recent sightings with coordinates:")
    for species, loc_name, lat, lng, radius in cursor.fetchall():
        logger.info(f"  {species} at {loc_name or 'Unknown'} - ({lat:.4f}, {lng:.4f}) - {radius} mi radius")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()