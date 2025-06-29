#!/usr/bin/env python3
"""Test the updated scraper to verify it collects coordinates."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from scrapers.llm_validator import LLMValidator
import json

def test_scraper_coordinates():
    """Test if the scraper now collects coordinates."""
    
    # Initialize scraper (it creates its own validator)
    scraper = RedditScraper()
    
    # Test with a single subreddit, limited posts
    print("Testing updated scraper with coordinate extraction...")
    
    # Clear any existing cache to force fresh processing
    cache_file = 'data/cache/reddit_posts_coloradohikers.json'
    if os.path.exists(cache_file):
        print(f"Removing old cache: {cache_file}")
        os.remove(cache_file)
    
    # Scrape with limited lookback for testing
    # Note: We can't control subreddits or max posts in current implementation
    sightings = scraper.scrape(lookback_days=7)
    
    print(f"\nFound {len(sightings)} sightings")
    
    # Check which sightings have coordinates
    with_coords = 0
    without_coords = 0
    
    for s in sightings:
        if s.get('coordinates'):
            with_coords += 1
            print(f"\n✓ WITH coordinates: {s['species']} at {s.get('location_name')}")
            print(f"  Coordinates: {s['coordinates']}")
            print(f"  Radius: {s.get('location_confidence_radius')} miles")
        else:
            without_coords += 1
            print(f"\n✗ WITHOUT coordinates: {s['species']} at {s.get('location_name')}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total sightings: {len(sightings)}")
    print(f"With coordinates: {with_coords}")
    print(f"Without coordinates: {without_coords}")
    
    # Save results for inspection
    with open('test_coordinates_results.json', 'w') as f:
        json.dump(sightings, f, indent=2, default=str)
    print(f"\nResults saved to test_coordinates_results.json")

if __name__ == "__main__":
    test_scraper_coordinates()