#!/usr/bin/env python3
"""
Run the Reddit scraper with LLM validation.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scrapers.reddit_scraper import RedditScraper
from loguru import logger

# Configure logging
logger.add("logs/reddit_scrape_{time}.log", rotation="10 MB")

def main():
    """Run Reddit scraper and save results."""
    logger.info("Starting Reddit scraper with LLM validation...")
    
    # Initialize scraper
    scraper = RedditScraper()
    
    # Check if Reddit API is available
    if not scraper.reddit:
        logger.error("Reddit API not available. Please check your credentials.")
        return
    
    # Scrape recent posts (last 7 days)
    logger.info("Scraping Reddit posts from the last 7 days...")
    sightings = scraper.scrape(lookback_days=7)
    
    # Log summary
    logger.info(f"\nScraping complete!")
    logger.info(f"Total sightings found: {len(sightings)}")
    
    # Count location data
    with_gmu = sum(1 for s in sightings if 'gmu_number' in s)
    with_coords = sum(1 for s in sightings if 'coordinates' in s)
    with_location = sum(1 for s in sightings if 'location_name' in s)
    
    logger.info(f"Sightings with GMU: {with_gmu}")
    logger.info(f"Sightings with coordinates: {with_coords}")
    logger.info(f"Sightings with location name: {with_location}")
    
    # Save results
    output_dir = Path("data/scraped")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"reddit_sightings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "scrape_date": datetime.now().isoformat(),
            "source": "reddit",
            "lookback_days": 7,
            "total_sightings": len(sightings),
            "sightings": sightings
        }, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Display sample sightings
    if sightings:
        logger.info("\nSample sightings:")
        for i, sighting in enumerate(sightings[:3]):
            logger.info(f"\n--- Sighting {i+1} ---")
            logger.info(f"Species: {sighting.get('species', 'unknown')}")
            logger.info(f"Confidence: {sighting.get('confidence', 0)*100:.0f}%")
            logger.info(f"GMU: {sighting.get('gmu_number', 'N/A')}")
            logger.info(f"Location: {sighting.get('location_name', 'N/A')}")
            logger.info(f"Coordinates: {sighting.get('coordinates', 'N/A')}")
            logger.info(f"Date: {sighting.get('sighting_date', 'N/A')}")
            logger.info(f"Source: r/{sighting.get('subreddit', 'unknown')}")

if __name__ == "__main__":
    main()