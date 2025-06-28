#!/usr/bin/env python3
"""
Test script to verify Reddit scraper is working properly with LLM validator.
Tests both cached and live extraction of wildlife sightings with location data.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scrapers.reddit_scraper import RedditScraper
from scrapers.llm_validator import LLMValidator
from loguru import logger

# Configure logging
logger.add("logs/test_reddit_llm_{time}.log", rotation="1 MB")

def test_llm_validator():
    """Test LLM validator directly with sample texts."""
    logger.info("Testing LLM Validator...")
    validator = LLMValidator()
    
    # Test cases with expected wildlife sightings
    test_cases = [
        {
            "text": "Just got back from a scouting trip in GMU 12. Saw a herd of about 20 elk near the Hermosa Creek drainage at 10,000 feet. Also spotted fresh bear tracks on the trail.",
            "expected_species": ["elk", "bear"],
            "expected_gmu": 12,
            "expected_location": "Hermosa Creek"
        },
        {
            "text": "Amazing morning hunt in unit 421! Tagged out on a nice 5x5 bull elk at first light. He was with a group of cows near the aspen grove at 11,200 feet elevation.",
            "expected_species": ["elk"],
            "expected_gmu": 421,
            "expected_elevation": 11200
        },
        {
            "text": "Trail cam caught 3 different bears last week near my stand in GMU 35. GPS coords: 39.4972, -106.8516. Lots of activity!",
            "expected_species": ["bear"],
            "expected_gmu": 35,
            "expected_coords": [39.4972, -106.8516]
        },
        {
            "text": "No luck today. Hiked all over Bear Lake trail but didn't see any wildlife. Maybe next time.",
            "expected_species": [],
            "should_be_sighting": False
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases):
        logger.info(f"\nTest Case {i+1}: {test_case['text'][:50]}...")
        
        # Test full text analysis
        result = validator.analyze_full_text_for_sighting(
            test_case['text'], 
            test_case.get('expected_species', [])
        )
        
        if result:
            logger.info(f"✓ Detected as sighting: {result['species']} (confidence: {result.get('confidence', 0)*100:.0f}%)")
            if 'gmu_number' in result:
                logger.info(f"  GMU: {result['gmu_number']}")
            if 'coordinates' in result:
                logger.info(f"  Coordinates: {result['coordinates']}")
            if 'elevation' in result:
                logger.info(f"  Elevation: {result['elevation']} ft")
            if 'location_name' in result:
                logger.info(f"  Location: {result['location_name']}")
        else:
            if test_case.get('should_be_sighting', True):
                logger.warning(f"✗ Not detected as sighting (expected to be detected)")
            else:
                logger.info(f"✓ Correctly identified as non-sighting")
        
        results.append({
            "test_case": i+1,
            "text": test_case['text'][:100] + "...",
            "result": result,
            "expected": test_case
        })
    
    return results

def test_reddit_scraper():
    """Test Reddit scraper with real or simulated data."""
    logger.info("\nTesting Reddit Scraper...")
    scraper = RedditScraper()
    
    # Check if Reddit API is available
    if scraper.reddit:
        logger.info("Reddit API is available - will use real data")
        # Test with 1-day lookback for quick results
        sightings = scraper.scrape(lookback_days=1)
    else:
        logger.error("Reddit API not available - cannot proceed with real data test")
        return []
    
    logger.info(f"\nFound {len(sightings)} total sightings")
    
    # Display sample sightings with location data
    for i, sighting in enumerate(sightings[:5]):  # Show first 5
        logger.info(f"\nSighting {i+1}:")
        logger.info(f"  Species: {sighting.get('species', 'unknown')}")
        logger.info(f"  Confidence: {sighting.get('confidence', 0)*100:.0f}%")
        logger.info(f"  Subreddit: r/{sighting.get('subreddit', 'unknown')}")
        logger.info(f"  Date: {sighting.get('sighting_date', 'unknown')}")
        
        # Location data
        if 'gmu_number' in sighting:
            logger.info(f"  GMU: {sighting['gmu_number']}")
        if 'coordinates' in sighting:
            logger.info(f"  Coordinates: {sighting['coordinates']}")
        if 'location_name' in sighting:
            logger.info(f"  Location: {sighting['location_name']}")
        if 'elevation' in sighting:
            logger.info(f"  Elevation: {sighting['elevation']} ft")
        
        logger.info(f"  Title: {sighting.get('reddit_post_title', 'N/A')[:80]}...")
        logger.info(f"  Text: {sighting.get('raw_text', 'N/A')[:100]}...")
    
    return sightings

def test_cache_functionality():
    """Test the caching system."""
    logger.info("\nTesting Cache Functionality...")
    validator = LLMValidator()
    
    # Get cache stats
    stats = validator.get_cache_stats()
    logger.info(f"Cache stats:")
    logger.info(f"  Total posts cached: {stats['total_posts_cached']}")
    logger.info(f"  Posts with sightings: {stats['posts_with_sightings']}")
    logger.info(f"  Total sightings: {stats['total_sightings']}")
    logger.info(f"  Cache file: {stats['cache_file']}")
    
    # Test cache hit/miss
    test_post_id = "test_post_123"
    test_content = "Saw 5 elk in GMU 12 this morning"
    
    # First check - should need processing
    should_process = validator.should_process_post(test_post_id, test_content)
    logger.info(f"\nFirst check - should process: {should_process}")
    
    # Update cache
    validator.update_cache(test_post_id, test_content, [{
        "species": "elk",
        "confidence": 0.9,
        "gmu_number": 12
    }])
    
    # Second check - should use cache
    should_process = validator.should_process_post(test_post_id, test_content)
    logger.info(f"Second check - should process: {should_process}")
    
    # Check with modified content
    should_process = validator.should_process_post(test_post_id, test_content + " and a bear")
    logger.info(f"Modified content - should process: {should_process}")

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Reddit Scraper + LLM Validator Integration Test")
    logger.info("=" * 60)
    
    # Test 1: LLM Validator
    logger.info("\n1. Testing LLM Validator...")
    llm_results = test_llm_validator()
    
    # Test 2: Cache functionality
    logger.info("\n2. Testing Cache System...")
    test_cache_functionality()
    
    # Test 3: Reddit Scraper
    logger.info("\n3. Testing Reddit Scraper Integration...")
    reddit_sightings = test_reddit_scraper()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    # Check if LLM is working
    validator = LLMValidator()
    if validator.llm_available:
        logger.info("✓ LLM Validator: AVAILABLE (using OpenAI)")
    else:
        logger.warning("✗ LLM Validator: NOT AVAILABLE (using fallback)")
    
    # Check if Reddit API is working
    scraper = RedditScraper()
    if scraper.reddit:
        logger.info("✓ Reddit API: AVAILABLE")
    else:
        logger.warning("✗ Reddit API: NOT AVAILABLE")
    
    # Check results
    if reddit_sightings:
        logger.info(f"✓ Wildlife Sightings Found: {len(reddit_sightings)}")
        
        # Count sightings with location data
        with_gmu = sum(1 for s in reddit_sightings if 'gmu_number' in s)
        with_coords = sum(1 for s in reddit_sightings if 'coordinates' in s)
        with_location = sum(1 for s in reddit_sightings if 'location_name' in s)
        
        logger.info(f"  - With GMU: {with_gmu}")
        logger.info(f"  - With coordinates: {with_coords}")
        logger.info(f"  - With location name: {with_location}")
    else:
        logger.warning("✗ No sightings found")
    
    # Save results
    output_file = "data/test_reddit_llm_results.json"
    results = {
        "test_date": datetime.now().isoformat(),
        "llm_available": validator.llm_available,
        "reddit_api_available": bool(scraper.reddit),
        "llm_test_results": llm_results,
        "sightings_found": len(reddit_sightings),
        "sample_sightings": reddit_sightings[:5] if reddit_sightings else []
    }
    
    os.makedirs("data", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()