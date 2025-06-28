#!/usr/bin/env python3
"""
Quick test of Reddit scraper - processes just a few posts to verify functionality.
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
logger.add("logs/quick_reddit_test_{time}.log", rotation="10 MB")

def main():
    """Run quick Reddit scraper test."""
    logger.info("Starting quick Reddit scraper test...")
    
    # Initialize scraper
    scraper = RedditScraper()
    
    # Check if Reddit API is available
    if not scraper.reddit:
        logger.error("Reddit API not available. Please check your credentials.")
        return
    
    # Override to scrape just 1 day and limit posts
    logger.info("Scraping limited Reddit posts (last 1 day, max 5 posts per subreddit)...")
    
    # Just test 2 subreddits for quick results
    test_subreddits = ['cohunting', 'elkhunting']
    
    # Scrape with custom limit
    sightings = []
    for subreddit in test_subreddits:
        logger.info(f"Scraping r/{subreddit}...")
        subreddit_sightings = scraper._scrape_subreddit(subreddit, lookback_days=1)
        sightings.extend(subreddit_sightings)
        # Break after getting some sightings to speed up test
        if len(sightings) >= 3:
            logger.info("Found enough sightings for quick test")
            break
    
    # Log summary
    logger.info(f"\nQuick test complete!")
    logger.info(f"Total sightings found: {len(sightings)}")
    
    # Count location data
    with_gmu = sum(1 for s in sightings if 'gmu_number' in s)
    with_coords = sum(1 for s in sightings if 'coordinates' in s)
    with_location = sum(1 for s in sightings if 'location_name' in s)
    
    logger.info(f"Sightings with GMU: {with_gmu}")
    logger.info(f"Sightings with coordinates: {with_coords}")
    logger.info(f"Sightings with location name: {with_location}")
    
    # Display all sightings found
    if sightings:
        logger.info("\nSightings found:")
        for i, sighting in enumerate(sightings):
            logger.info(f"\n--- Sighting {i+1} ---")
            logger.info(f"Species: {sighting.get('species', 'unknown')}")
            logger.info(f"Confidence: {sighting.get('confidence', 0)*100:.0f}%")
            logger.info(f"GMU: {sighting.get('gmu_number', 'N/A')}")
            logger.info(f"Location: {sighting.get('location_name', 'N/A')}")
            logger.info(f"Coordinates: {sighting.get('coordinates', 'N/A')}")
            logger.info(f"Elevation: {sighting.get('elevation', 'N/A')}")
            logger.info(f"Date: {sighting.get('sighting_date', 'N/A')}")
            logger.info(f"Source: r/{sighting.get('subreddit', 'unknown')}")
            logger.info(f"Post Title: {sighting.get('reddit_post_title', 'N/A')[:80]}...")
            logger.info(f"Text excerpt: {sighting.get('raw_text', 'N/A')[:150]}...")
    else:
        logger.info("\nNo sightings found in this quick test.")
    
    # Save results
    output_dir = Path("data/scraped")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"quick_reddit_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "source": "reddit_quick_test",
            "subreddits": test_subreddits,
            "lookback_days": 1,
            "max_posts_per_subreddit": 5,
            "total_sightings": len(sightings),
            "sightings": sightings
        }, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Show cache stats
    cache_stats = scraper.validator.get_cache_stats()
    logger.info(f"\nCache statistics:")
    logger.info(f"Total posts in cache: {cache_stats['total_posts_cached']}")
    logger.info(f"Posts with sightings: {cache_stats['posts_with_sightings']}")

if __name__ == "__main__":
    main()