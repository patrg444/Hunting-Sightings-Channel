#!/usr/bin/env python3
"""
Script to run Google Places scraper for wildlife sightings.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from loguru import logger
from scrapers.google_places_scraper import GooglePlacesScraper
from processors import GMUProcessor, TrailProcessor
from scripts.sightings_cli import map_sighting_to_gmu

def main():
    """Run Google Places scraper and display results."""
    logger.info("=== Google Places Wildlife Sightings Scraper ===")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize processors
        logger.info("Loading GMU and trail data...")
        gmu_processor = GMUProcessor("data/gmu/colorado_gmu_sample.geojson")
        gmu_processor.load_gmu_data()
        
        trail_processor = TrailProcessor()
        trail_processor.load_trail_index()
        
        # Run scraper
        logger.info("Running Google Places scraper...")
        scraper = GooglePlacesScraper()
        sightings = scraper.scrape(lookback_days=1)  # Will scrape latest 5 reviews per place
        
        # Map to GMUs
        logger.info("Mapping sightings to GMUs...")
        for sighting in sightings:
            sighting['gmu_unit'] = map_sighting_to_gmu(
                sighting, trail_processor, gmu_processor
            )
        
        # Display results
        logger.success(f"Found {len(sightings)} total sightings")
        
        if sightings:
            logger.info("\nSample sightings:")
            for i, sighting in enumerate(sightings[:5]):  # Show first 5
                logger.info(f"\n--- Sighting {i+1} ---")
                logger.info(f"Species: {sighting.get('species', 'Unknown')}")
                logger.info(f"Location: {sighting.get('location_details', 'Unknown')}")
                logger.info(f"Location Radius: {sighting.get('location_confidence_radius', 'Unknown')} miles")
                logger.info(f"GMU: {sighting.get('gmu_unit', 'Unknown')}")
                logger.info(f"Source: {sighting.get('trail_name', 'Unknown')}")
                logger.info(f"Date: {sighting.get('sighting_date', 'Unknown')}")
                logger.info(f"Context: {sighting.get('context', '')[:200]}...")
        
        # Save results
        from pathlib import Path
        import json
        
        output_dir = Path("data/sightings")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"google_places_sightings_{timestamp}.json"
        
        # Convert datetime objects to strings
        for sighting in sightings:
            if 'sighting_date' in sighting:
                if hasattr(sighting['sighting_date'], 'isoformat'):
                    sighting['sighting_date'] = sighting['sighting_date'].isoformat()
                elif hasattr(sighting['sighting_date'], 'strftime'):
                    sighting['sighting_date'] = sighting['sighting_date'].strftime('%Y-%m-%d')
            if 'extracted_at' in sighting and hasattr(sighting['extracted_at'], 'isoformat'):
                sighting['extracted_at'] = sighting['extracted_at'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(sightings, f, indent=2)
        
        logger.info(f"\nSaved sightings to {output_file}")
        
        # Show statistics
        species_count = {}
        for sighting in sightings:
            species = sighting.get('species', 'unknown')
            species_count[species] = species_count.get(species, 0) + 1
        
        logger.info(f"\nSpecies breakdown:")
        for species, count in sorted(species_count.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {species}: {count}")
            
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        
    logger.info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()