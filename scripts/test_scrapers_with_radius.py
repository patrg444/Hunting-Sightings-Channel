#!/usr/bin/env python3
"""
Test Google Places and 14ers scrapers with location confidence radius feature.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.google_places_scraper import GooglePlacesScraper
from scrapers.fourteeners_scraper_real import FourteenersRealScraper
from scrapers.llm_validator import LLMValidator

def test_google_places_scraper():
    """Test Google Places scraper with radius feature."""
    logger.info("="*60)
    logger.info("Testing Google Places Scraper")
    logger.info("="*60)
    
    # Check for API key
    if not os.getenv('GOOGLE_PLACES_API_KEY'):
        logger.error("GOOGLE_PLACES_API_KEY not set!")
        logger.info("Google Places scraper requires an API key from Google Cloud Console")
        return []
    
    try:
        scraper = GooglePlacesScraper()
        logger.success("✓ Google Places scraper initialized")
        
        # Check if LLM validator is available
        if scraper.llm_validator.llm_available:
            logger.success("✓ LLM validator available for wildlife detection")
        else:
            logger.warning("⚠ LLM validator not available - basic keyword matching only")
        
        # Run scraper
        logger.info("\nFetching recent reviews from Colorado trailheads...")
        sightings = scraper.scrape(lookback_days=7)
        
        logger.info(f"\nFound {len(sightings)} wildlife sightings")
        
        # Check for radius data
        radius_count = 0
        for sighting in sightings:
            if sighting.get('location_confidence_radius'):
                radius_count += 1
                logger.info(f"\n✓ Sighting with radius:")
                logger.info(f"  Species: {sighting.get('species')}")
                logger.info(f"  Location: {sighting.get('location_name', 'N/A')}")
                logger.info(f"  Confidence radius: {sighting.get('location_confidence_radius')} miles")
                logger.info(f"  Review excerpt: {sighting.get('raw_text', '')[:100]}...")
        
        if radius_count == 0:
            logger.warning("No sightings with location confidence radius found")
            logger.info("This could mean no wildlife was mentioned in recent reviews")
        else:
            logger.success(f"✓ {radius_count}/{len(sightings)} sightings have location confidence radius")
        
        return sightings
        
    except Exception as e:
        logger.error(f"Google Places scraper failed: {e}")
        return []

def test_fourteeners_scraper():
    """Test 14ers scraper with radius feature."""
    logger.info("\n" + "="*60)
    logger.info("Testing 14ers Scraper")
    logger.info("="*60)
    
    try:
        scraper = FourteenersRealScraper()
        logger.success("✓ 14ers scraper initialized")
        
        # Check if LLM validator is available
        validator = LLMValidator()
        if validator.llm_available:
            logger.success("✓ LLM validator available for wildlife detection")
        else:
            logger.warning("⚠ LLM validator not available")
        
        # Run scraper
        logger.info("\nFetching recent trip reports from 14ers.com...")
        sightings = scraper.scrape(lookback_days=30)  # Look back further for 14ers
        
        logger.info(f"\nFound {len(sightings)} wildlife mentions")
        
        # Process with LLM if available
        if validator.llm_available and sightings:
            logger.info("\nProcessing sightings with LLM validator...")
            validated_sightings = []
            
            for sighting in sightings:
                # Validate with LLM
                is_valid, confidence, location_data = validator.validate_sighting_with_llm(
                    sighting.get('raw_text', ''),
                    sighting.get('keyword_matched', ''),
                    sighting.get('species', ''),
                    '14ers'  # Provide context
                )
                
                if is_valid and confidence > 0.7:
                    # Add location data to sighting
                    sighting['llm_validated'] = True
                    sighting['llm_confidence'] = confidence
                    if location_data:
                        sighting.update(location_data)
                    validated_sightings.append(sighting)
                    
                    if sighting.get('location_confidence_radius'):
                        logger.info(f"\n✓ Valid sighting with radius:")
                        logger.info(f"  Species: {sighting.get('species')}")
                        logger.info(f"  Peak: {sighting.get('peak_name', 'N/A')}")
                        logger.info(f"  Confidence radius: {sighting.get('location_confidence_radius')} miles")
                        logger.info(f"  Context: {sighting.get('raw_text', '')[:100]}...")
            
            radius_count = sum(1 for s in validated_sightings if s.get('location_confidence_radius'))
            logger.info(f"\n{radius_count}/{len(validated_sightings)} validated sightings have location radius")
            return validated_sightings
        else:
            logger.info("Returning raw sightings without LLM validation")
            return sightings
            
    except Exception as e:
        logger.error(f"14ers scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Run all tests."""
    logger.info("Testing Scrapers with Location Confidence Radius")
    logger.info("="*60)
    
    all_results = {
        'test_date': datetime.now().isoformat(),
        'google_places': [],
        '14ers': []
    }
    
    # Test Google Places
    logger.info("\n1. Google Places Scraper Test")
    google_results = test_google_places_scraper()
    all_results['google_places'] = google_results
    
    # Test 14ers
    logger.info("\n2. 14ers Scraper Test")
    fourteeners_results = test_fourteeners_scraper()
    all_results['14ers'] = fourteeners_results
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    google_radius_count = sum(1 for s in google_results if s.get('location_confidence_radius'))
    fourteeners_radius_count = sum(1 for s in fourteeners_results if s.get('location_confidence_radius'))
    
    logger.info(f"\nGoogle Places:")
    logger.info(f"  Total sightings: {len(google_results)}")
    logger.info(f"  With radius data: {google_radius_count}")
    
    logger.info(f"\n14ers.com:")
    logger.info(f"  Total sightings: {len(fourteeners_results)}")
    logger.info(f"  With radius data: {fourteeners_radius_count}")
    
    # Save results
    output_file = Path('data/sightings') / f'scraper_radius_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_file.parent.mkdir(exist_ok=True)
    
    # Clean datetime objects for JSON
    for results in [all_results['google_places'], all_results['14ers']]:
        for sighting in results:
            for key in ['sighting_date', 'extracted_at']:
                if key in sighting and hasattr(sighting[key], 'isoformat'):
                    sighting[key] = sighting[key].isoformat()
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.success(f"\nResults saved to: {output_file}")
    
    # Overall assessment
    total_with_radius = google_radius_count + fourteeners_radius_count
    if total_with_radius > 0:
        logger.success(f"\n✓ Location confidence radius is working! Found {total_with_radius} sightings with radius data.")
    else:
        logger.warning("\n⚠ No sightings with radius data found. This could be due to:")
        logger.info("  - No recent wildlife sightings in the data sources")
        logger.info("  - LLM validator not available (check OPENAI_API_KEY)")
        logger.info("  - Sources not having specific enough location descriptions")

if __name__ == "__main__":
    main()