#!/usr/bin/env python3
"""
Run Google Places scraper with option to clear cache for fresh analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from loguru import logger
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run Google Places scraper')
    parser.add_argument('--clear-cache', action='store_true', 
                        help='Clear the review cache before running')
    parser.add_argument('--show-all', action='store_true',
                        help='Show all sightings, not just first 5')
    args = parser.parse_args()
    
    if args.clear_cache:
        logger.warning("Clearing Google review cache...")
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM google_review_cache")
            conn.commit()
            count = cursor.rowcount
            conn.close()
            logger.success(f"Cleared {count} cached reviews")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return
    
    # Now run the regular scraper
    from scrapers.google_places_scraper import GooglePlacesScraper
    from processors import GMUProcessor, TrailProcessor
    from scripts.sightings_cli import map_sighting_to_gmu
    
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
        sightings = scraper.scrape(lookback_days=1)
        
        # Map to GMUs
        logger.info("Mapping sightings to GMUs...")
        for sighting in sightings:
            sighting['gmu_unit'] = map_sighting_to_gmu(
                sighting, trail_processor, gmu_processor
            )
        
        # Display results
        logger.success(f"Found {len(sightings)} total sightings")
        
        if sightings:
            show_limit = None if args.show_all else 10
            logger.info(f"\nSightings {'(all)' if args.show_all else '(first 10)'}:")
            
            for i, sighting in enumerate(sightings[:show_limit]):
                logger.info(f"\n--- Sighting {i+1} ---")
                logger.info(f"Species: {sighting.get('species', 'Unknown')}")
                location = sighting.get('location_details', {})
                if isinstance(location, dict):
                    logger.info(f"Location: {location.get('location_name', 'Unknown')}")
                else:
                    logger.info(f"Location: {location}")
                logger.info(f"Confidence Radius: {sighting.get('location_confidence_radius', 'Unknown')} miles")
                logger.info(f"GMU: {sighting.get('gmu_unit', 'Unknown')}")
                logger.info(f"Trail: {sighting.get('trail_name', 'Unknown')}")
                logger.info(f"Date: {sighting.get('sighting_date', 'Unknown')}")
                context = sighting.get('context', '')
                if context:
                    logger.info(f"Context: {context[:200]}{'...' if len(context) > 200 else ''}")
        
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
        locations_count = {}
        
        for sighting in sightings:
            # Count by species
            species = sighting.get('species', 'unknown')
            species_count[species] = species_count.get(species, 0) + 1
            
            # Count by location
            trail = sighting.get('trail_name', 'unknown')
            locations_count[trail] = locations_count.get(trail, 0) + 1
        
        logger.info(f"\nSpecies breakdown:")
        for species, count in sorted(species_count.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {species}: {count}")
            
        logger.info(f"\nTop locations with sightings:")
        for location, count in sorted(locations_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {location}: {count}")
            
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        
    logger.info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()