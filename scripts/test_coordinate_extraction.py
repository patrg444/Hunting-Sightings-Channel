#\!/usr/bin/env python3
"""
Test that scrapers are extracting coordinates correctly.
"""

from scrapers.reddit_scraper import RedditScraper
from scrapers.database_saver import save_sightings_to_db
from loguru import logger
import json

def main():
    logger.info("Testing Reddit scraper with coordinate extraction...")
    
    # Initialize scraper
    scraper = RedditScraper()
    
    # Scrape recent posts
    sightings = scraper.scrape(lookback_days=1)
    logger.info(f"Found {len(sightings)} sightings")
    
    # Check for coordinates
    with_coords = 0
    with_radius = 0
    
    for s in sightings:
        if s.get('coordinates'):
            with_coords += 1
        if s.get('location_confidence_radius'):
            with_radius += 1
            
        # Show details for first few
        if with_coords <= 3 and s.get('coordinates'):
            logger.info(f"\nSighting with coordinates:")
            logger.info(f"  Species: {s.get('species')}")
            logger.info(f"  Location: {s.get('location_name', 'Unknown')}")
            logger.info(f"  Coordinates: {s.get('coordinates')}")
            logger.info(f"  Radius: {s.get('location_confidence_radius')} miles")
            logger.info(f"  Description: {s.get('raw_text', '')[:100]}...")
    
    logger.info(f"\nSummary:")
    logger.info(f"  Total sightings: {len(sightings)}")
    logger.info(f"  With coordinates: {with_coords} ({with_coords/len(sightings)*100:.1f}%)")
    logger.info(f"  With radius: {with_radius} ({with_radius/len(sightings)*100:.1f}%)")
    
    # Save to database
    if sightings:
        logger.info("\nSaving to database...")
        saved = save_sightings_to_db(sightings, "reddit_test")
        logger.info(f"Saved {saved} sightings")

if __name__ == "__main__":
    main()