#!/usr/bin/env python3
"""
Test the iNaturalist scraper to ensure it returns data in the correct format.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from scrapers.inaturalist_scraper import INaturalistScraper
import json

def test_scraper():
    """Test the iNaturalist scraper."""
    
    logger.info("Testing iNaturalist scraper...")
    
    try:
        # Initialize scraper
        scraper = INaturalistScraper()
        logger.success("✓ Scraper initialized")
        
        # Check LLM validator
        if hasattr(scraper, 'llm_validator'):
            logger.success(f"✓ Has LLM validator")
            logger.info(f"  Model: {scraper.llm_validator.model}")
        else:
            logger.warning("✗ No LLM validator")
        
        # Run scraper for 7 days to get more data
        logger.info("\nFetching recent observations (7 day lookback)...")
        sightings = scraper.scrape(lookback_days=7)
        
        if sightings:
            logger.success(f"Found {len(sightings)} sightings!")
            
            # Check the format of the first sighting
            sighting = sightings[0]
            logger.info("\nFirst sighting format check:")
            
            # Required fields
            required_fields = [
                'species', 'raw_text', 'keyword_matched', 'source_url', 
                'source_type', 'extracted_at', 'location_name', 'sighting_date'
            ]
            
            # LLM fields
            llm_fields = [
                'confidence', 'llm_validated', 'location_confidence_radius'
            ]
            
            # Coordinate fields
            coord_fields = ['latitude', 'longitude']
            
            logger.info("Required fields:")
            for field in required_fields:
                if field in sighting:
                    value = str(sighting[field])[:50] + "..." if len(str(sighting[field])) > 50 else sighting[field]
                    logger.success(f"  ✓ {field}: {value}")
                else:
                    logger.error(f"  ✗ {field}: MISSING")
            
            logger.info("\nLLM fields:")
            for field in llm_fields:
                if field in sighting:
                    logger.success(f"  ✓ {field}: {sighting[field]}")
                else:
                    logger.error(f"  ✗ {field}: MISSING")
            
            logger.info("\nCoordinate fields:")
            for field in coord_fields:
                if field in sighting:
                    logger.success(f"  ✓ {field}: {sighting[field]}")
                else:
                    logger.warning(f"  - {field}: Not present")
            
            # Show species breakdown
            species_count = {}
            for s in sightings:
                species = s.get('species', 'unknown')
                species_count[species] = species_count.get(species, 0) + 1
            
            logger.info(f"\nSpecies found:")
            for species, count in sorted(species_count.items()):
                logger.info(f"  - {species}: {count}")
            
            # Print first sighting for inspection
            logger.info("\nFull first sighting data:")
            print(json.dumps(sighting, indent=2, default=str))
            
        else:
            logger.warning("No sightings found in the last day")
            logger.info("This is normal - iNaturalist may not have recent observations")
            logger.info("Try increasing lookback_days for more results")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper()