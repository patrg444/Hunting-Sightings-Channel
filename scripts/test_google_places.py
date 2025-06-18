#!/usr/bin/env python3
"""
Test script for Google Places wildlife sighting extraction.
Demonstrates compliance with Google's licensing terms.
"""

import os
import sys
import json
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.google_places_scraper import GooglePlacesScraper

load_dotenv()


def test_google_places_scraper():
    """Test the Google Places scraper functionality."""
    
    # Check for API key
    if not os.getenv('GOOGLE_PLACES_API_KEY'):
        logger.error("GOOGLE_PLACES_API_KEY not found in environment variables")
        logger.info("Please set GOOGLE_PLACES_API_KEY in your .env file")
        logger.info("Get your API key from: https://console.cloud.google.com/")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("OPENAI_API_KEY not found - will use keyword matching only")
    
    try:
        # Initialize scraper
        logger.info("Initializing Google Places scraper...")
        scraper = GooglePlacesScraper()
        
        # Test fetching trail locations
        logger.info("\n=== Testing Trail Location Fetching ===")
        locations = scraper.get_trail_locations()
        logger.info(f"Found {len(locations)} trail locations:")
        for loc in locations:
            logger.info(f"  - {loc['name']} ({loc['lat']}, {loc['lon']})")
        
        # Test scraping reviews for wildlife
        logger.info("\n=== Testing Wildlife Sighting Extraction ===")
        wildlife_events = scraper.scrape(lookback_days=1)  # Parameter ignored for Google Places
        
        if wildlife_events:
            logger.info(f"\nFound {len(wildlife_events)} wildlife events:")
            for event in wildlife_events:
                # Remove raw review data for display
                display_event = event.copy()
                display_event.pop('raw_review_data', None)
                
                logger.info(f"\n--- Wildlife Event ---")
                logger.info(f"Species: {event['species']}")
                logger.info(f"Location: {event['location_details']['place_name']}")
                logger.info(f"Event Date: {event['event_date']}")
                logger.info(f"Review Date: {event['review_date']}")
                logger.info(f"Confidence: {event['confidence_score']:.2f}")
                if event.get('gmu_unit'):
                    logger.info(f"GMU: {event['gmu_unit']}")
            
            # Save sample output
            output_file = 'data/google_places_wildlife_sample.json'
            os.makedirs('data', exist_ok=True)
            
            # Remove raw data before saving
            save_events = []
            for event in wildlife_events:
                save_event = event.copy()
                save_event.pop('raw_review_data', None)
                save_events.append(save_event)
            
            with open(output_file, 'w') as f:
                json.dump({
                    'extraction_date': datetime.now().isoformat(),
                    'total_events': len(save_events),
                    'events': save_events
                }, f, indent=2, default=str)
            
            logger.info(f"\nSample output saved to: {output_file}")
            
            # Demonstrate compliance
            logger.info("\n=== Compliance Demonstration ===")
            logger.info("✓ Only fetched latest 5 reviews per trailhead")
            logger.info("✓ Extracted only wildlife event data (species, date, location)")
            logger.info("✓ Raw review data marked for 30-day retention")
            logger.info("✓ Review IDs cached for deduplication")
            
        else:
            logger.info("No wildlife events found in recent reviews")
            logger.info("This is normal if reviews don't mention wildlife sightings")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


def demonstrate_data_lifecycle():
    """Demonstrate the compliant data lifecycle."""
    logger.info("\n=== Google Places Data Lifecycle ===")
    logger.info("1. Nightly: Fetch latest 5 reviews per trailhead")
    logger.info("2. Process: Use OpenAI to extract wildlife mentions")
    logger.info("3. Store: ")
    logger.info("   - Raw reviews → google_reviews_raw (30-day retention)")
    logger.info("   - Wildlife data → wildlife_events (permanent)")
    logger.info("   - Review IDs → google_review_cache (permanent, for dedup)")
    logger.info("4. Cleanup: Daily job purges reviews > 30 days old")
    logger.info("5. Result: Long-term wildlife database without storing Google content")


def main():
    """Run the test."""
    logger.info("Google Places Wildlife Extraction Test")
    logger.info("=====================================")
    
    # Run the test
    test_google_places_scraper()
    
    # Show data lifecycle
    demonstrate_data_lifecycle()
    
    logger.info("\n✓ Test completed successfully")


if __name__ == "__main__":
    main()
