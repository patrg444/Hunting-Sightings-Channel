#!/usr/bin/env python3
"""
Test Reddit scraper with location confidence radius feature.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from scrapers.llm_validator import LLMValidator

def test_reddit_with_radius():
    """Test Reddit scraper with location confidence radius."""
    
    logger.info("============================================================")
    logger.info("Testing Reddit Scraper with Location Confidence Radius")
    logger.info("============================================================\n")
    
    # Initialize components
    logger.info("Initializing Reddit scraper and LLM validator...")
    scraper = RedditScraper()
    validator = LLMValidator()
    
    if not validator.llm_available:
        logger.error("LLM validator not available. Please set OPENAI_API_KEY environment variable.")
        return
    
    logger.success("LLM validator initialized successfully!")
    
    # Test with specific Reddit posts
    test_posts = [
        {
            "title": "Elk sighting at specific location",
            "text": "Just saw a massive bull elk at the bridge crossing on Maroon Creek Trail at mile marker 3.5. He was about 50 yards from the trail.",
            "subreddit": "COhunting",
            "expected_radius_range": (0.5, 2)  # Very specific location
        },
        {
            "title": "Bear near town",
            "text": "Bear activity reported near the town of Aspen. Multiple sightings in the last week around the ski area.",
            "subreddit": "ColoradoHiking", 
            "expected_radius_range": (5, 15)  # Town area
        },
        {
            "title": "Deer in GMU",
            "text": "Saw some deer somewhere in unit 23 while scouting. Not sure exactly where but definitely in the unit.",
            "subreddit": "COhunting",
            "expected_radius_range": (20, 50)  # GMU only
        },
        {
            "title": "Specific GPS coordinates",
            "text": "Mountain goat spotted at 39.1174° N, 106.4453° W near the summit. Amazing to see at 13,500 feet!",
            "subreddit": "14ers",
            "expected_radius_range": (0.5, 1)  # GPS coordinates
        }
    ]
    
    results = []
    
    logger.info("\nProcessing test cases...\n")
    
    for i, test_case in enumerate(test_posts, 1):
        logger.info(f"Test Case {i}: {test_case['title']}")
        logger.info(f"Subreddit: r/{test_case['subreddit']}")
        logger.info(f"Text: {test_case['text'][:100]}...")
        
        # Find species mentioned
        species_keywords = ['elk', 'bear', 'deer', 'goat', 'mountain goat']
        species_found = [s for s in species_keywords if s in test_case['text'].lower()]
        
        # Analyze with LLM
        result = validator.analyze_full_text_for_sighting(
            test_case['text'],
            species_found,
            test_case['subreddit']
        )
        
        if result:
            logger.success(f"✓ Valid sighting detected!")
            logger.info(f"  Species: {result.get('species')}")
            logger.info(f"  Confidence: {result.get('confidence', 0) * 100:.0f}%")
            logger.info(f"  Location: {result.get('location_name', 'N/A')}")
            logger.info(f"  GMU: {result.get('gmu_number', 'N/A')}")
            
            radius = result.get('location_confidence_radius')
            if radius:
                logger.info(f"  Location confidence radius: {radius} miles")
                expected_min, expected_max = test_case['expected_radius_range']
                if expected_min <= radius <= expected_max:
                    logger.success(f"  ✓ Radius within expected range ({expected_min}-{expected_max} miles)")
                else:
                    logger.warning(f"  ⚠ Radius outside expected range ({expected_min}-{expected_max} miles)")
            else:
                logger.warning("  No radius returned")
                
            result['test_case'] = test_case['title']
            result['subreddit'] = test_case['subreddit']
            results.append(result)
        else:
            logger.warning("✗ Not detected as valid sighting")
            
        logger.info("")
    
    # Now test with real Reddit data if available
    if scraper.reddit:
        logger.info("\n" + "="*60)
        logger.info("Testing with real Reddit data...")
        logger.info("="*60 + "\n")
        
        # Get recent posts
        subreddits = ['COhunting', 'ColoradoHiking', '14ers']
        real_results = []
        
        for subreddit_name in subreddits:
            try:
                logger.info(f"\nChecking r/{subreddit_name}...")
                subreddit = scraper.reddit.subreddit(subreddit_name)
                
                # Get last 10 posts
                for submission in subreddit.new(limit=10):
                    # Check if post might contain wildlife
                    full_text = f"{submission.title} {submission.selftext}"
                    
                    # Quick keyword check
                    wildlife_keywords = ['elk', 'deer', 'bear', 'moose', 'mountain goat', 'bighorn', 'sheep']
                    if any(keyword in full_text.lower() for keyword in wildlife_keywords):
                        logger.info(f"\nFound potential sighting: {submission.title[:60]}...")
                        
                        species_found = [k for k in wildlife_keywords if k in full_text.lower()]
                        
                        result = validator.analyze_full_text_for_sighting(
                            full_text[:1500],  # Limit length
                            species_found,
                            subreddit_name
                        )
                        
                        if result:
                            logger.success("✓ Valid sighting!")
                            logger.info(f"  Species: {result.get('species')}")
                            logger.info(f"  Confidence: {result.get('confidence', 0) * 100:.0f}%")
                            logger.info(f"  Location radius: {result.get('location_confidence_radius', 'N/A')} miles")
                            
                            result['reddit_title'] = submission.title
                            result['reddit_url'] = f"https://reddit.com{submission.permalink}"
                            result['subreddit'] = subreddit_name
                            real_results.append(result)
                            
            except Exception as e:
                logger.error(f"Error accessing r/{subreddit_name}: {e}")
        
        # Save all results
        all_results = {
            'test_cases': results,
            'real_reddit': real_results,
            'timestamp': datetime.now().isoformat()
        }
        
        output_file = Path('data/sightings') / f'reddit_radius_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
            
        logger.success(f"\nResults saved to: {output_file}")
        
        # Summary statistics
        if real_results:
            radii = [r['location_confidence_radius'] for r in real_results if r.get('location_confidence_radius')]
            if radii:
                logger.info("\nLocation Confidence Radius Statistics:")
                logger.info(f"  Min: {min(radii)} miles")
                logger.info(f"  Max: {max(radii)} miles") 
                logger.info(f"  Average: {sum(radii)/len(radii):.1f} miles")
                logger.info(f"  Total sightings with radius: {len(radii)}/{len(real_results)}")
    
    else:
        logger.warning("Reddit API not available for real data testing")

if __name__ == "__main__":
    test_reddit_with_radius()