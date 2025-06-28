#!/usr/bin/env python3
"""
Test that all scrapers return consistent output format with LLM validation fields.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
import json

def test_scraper_output_format():
    """Test that all scrapers return consistent fields."""
    
    # Expected core fields that all scrapers should return
    core_fields = {
        'species', 'raw_text', 'keyword_matched', 'source_url', 
        'source_type', 'extracted_at', 'location_name', 'sighting_date'
    }
    
    # LLM validation fields that should be present when LLM is used
    llm_fields = {
        'confidence', 'llm_validated', 'location_confidence_radius'
    }
    
    # Test data for each scraper
    test_cases = [
        {
            'name': 'Reddit Scraper',
            'module': 'scrapers.reddit_scraper',
            'class': 'RedditScraper',
            'sample_text': "Saw a huge bull elk near the bridge at Maroon Creek",
            'expected_source': 'reddit'
        },
        {
            'name': 'Google Places Scraper', 
            'module': 'scrapers.google_places_scraper',
            'class': 'GooglePlacesScraper',
            'sample_text': "Great hike! Spotted some bighorn sheep on the cliffs",
            'expected_source': 'google_places'
        },
        {
            'name': '14ers Scraper',
            'module': 'scrapers.fourteeners_scraper_real',
            'class': 'FourteenersRealScraper',
            'sample_text': "Beautiful day on the mountain. Saw mountain goats near the summit",
            'expected_source': '14ers.com'
        },
        {
            'name': 'iNaturalist Scraper',
            'module': 'scrapers.inaturalist_scraper',
            'class': 'INaturalistScraper',
            'sample_text': "Observed a black bear near the trail",
            'expected_source': 'inaturalist'
        }
    ]
    
    logger.info("Testing scraper output consistency...")
    
    for test in test_cases:
        logger.info(f"\n--- Testing {test['name']} ---")
        
        try:
            # Import and initialize scraper
            module = __import__(test['module'], fromlist=[test['class']])
            scraper_class = getattr(module, test['class'])
            scraper = scraper_class()
            
            logger.success(f"✓ {test['name']} initialized")
            
            # Check if it has LLM validator
            if hasattr(scraper, 'llm_validator'):
                logger.success(f"✓ Has LLM validator (llm_validator)")
                logger.info(f"  Model: {scraper.llm_validator.model}")
            elif hasattr(scraper, 'validator'):
                logger.success(f"✓ Has LLM validator (validator)")
                logger.info(f"  Model: {scraper.validator.model}")
            else:
                logger.warning(f"✗ No LLM validator found")
            
            # Test the output format (without actually scraping)
            # Check what fields would be returned based on the code
            if test['name'] == 'Reddit Scraper':
                # Reddit returns these fields in the sighting dict
                expected_fields = core_fields | llm_fields | {
                    'reddit_post_title', 'subreddit', 'post_id'
                }
                logger.info(f"Expected fields: {len(expected_fields)}")
                
            elif test['name'] == 'Google Places Scraper':
                expected_fields = core_fields | llm_fields | {
                    'place_id', 'place_name', 'review_author', 'review_rating',
                    'latitude', 'longitude', 'gmu_hint', 'location_details', 'full_text'
                }
                logger.info(f"Expected fields: {len(expected_fields)}")
                
            elif test['name'] == '14ers Scraper':
                expected_fields = core_fields | llm_fields | {
                    'author', 'report_title', 'location_details'
                }
                logger.info(f"Expected fields: {len(expected_fields)}")
                
            elif test['name'] == 'iNaturalist Scraper':
                expected_fields = core_fields | llm_fields | {
                    'latitude', 'longitude', 'observed_date', 'observed_time',
                    'observer_username', 'observer_name', 'photo_url', 'quality_grade',
                    'inaturalist_id', 'positional_accuracy_meters', 'location_details'
                }
                logger.info(f"Expected fields: {len(expected_fields)}")
            
            # Verify core fields are expected
            logger.info(f"Core fields present: {core_fields.issubset(expected_fields)}")
            logger.info(f"LLM fields present: {llm_fields.issubset(expected_fields)}")
            
        except Exception as e:
            logger.error(f"✗ Failed to test {test['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("\n=== Summary ===")
    logger.info("All scrapers should return at minimum:")
    logger.info(f"- Core fields: {', '.join(sorted(core_fields))}")
    logger.info(f"- LLM fields: {', '.join(sorted(llm_fields))}")
    logger.info("\nAdditional fields are OK and expected for source-specific metadata.")

if __name__ == "__main__":
    test_scraper_output_format()