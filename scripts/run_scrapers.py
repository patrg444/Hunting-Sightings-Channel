#!/usr/bin/env python3
"""
Script to run all scrapers and save results.
This would typically be scheduled to run daily at 2 AM MT.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Dict, Any
import json
from pathlib import Path
from loguru import logger

from scrapers import FourteenersRealScraper, RedditScraper
from processors import GMUProcessor, TrailProcessor
from scripts.sightings_cli import map_sighting_to_gmu


def run_all_scrapers(lookback_days: int = 1) -> List[Dict[str, Any]]:
    """
    Run all enabled scrapers and collect sightings.
    
    Args:
        lookback_days: Days to look back for content
        
    Returns:
        Combined list of all sightings with GMU mapping
    """
    all_sightings = []
    
    # Initialize processors
    logger.info("Loading GMU and trail data...")
    gmu_processor = GMUProcessor("data/gmu/colorado_gmu_sample.geojson")
    gmu_processor.load_gmu_data()
    
    trail_processor = TrailProcessor()
    trail_processor.load_trail_index()
    
    # Run each scraper
    scrapers = [
        ('14ers.com', FourteenersRealScraper),
        ('Reddit', RedditScraper)
    ]
    
    for name, scraper_class in scrapers:
        logger.info(f"Running {name} scraper...")
        try:
            scraper = scraper_class()
            sightings = scraper.scrape(lookback_days)
            
            # Map to GMUs
            for sighting in sightings:
                sighting['gmu_unit'] = map_sighting_to_gmu(
                    sighting, trail_processor, gmu_processor
                )
            
            all_sightings.extend(sightings)
            logger.success(f"{name}: Found {len(sightings)} sightings")
            
        except Exception as e:
            logger.error(f"Error scraping {name}: {e}")
    
    return all_sightings


def save_sightings(sightings: List[Dict[str, Any]]):
    """
    Save sightings to JSON file (in production, this would save to database).
    
    Args:
        sightings: List of sighting dictionaries
    """
    # Create data directory if needed
    output_dir = Path("data/sightings")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"sightings_{timestamp}.json"
    
    # Convert datetime objects to strings for JSON serialization
    for sighting in sightings:
        if 'sighting_date' in sighting and hasattr(sighting['sighting_date'], 'isoformat'):
            sighting['sighting_date'] = sighting['sighting_date'].isoformat()
        if 'extracted_at' in sighting and hasattr(sighting['extracted_at'], 'isoformat'):
            sighting['extracted_at'] = sighting['extracted_at'].isoformat()
    
    with open(output_file, 'w') as f:
        json.dump(sightings, f, indent=2)
    
    logger.info(f"Saved {len(sightings)} sightings to {output_file}")
    
    # Also save a "latest" file for easy access
    latest_file = output_dir / "latest_sightings.json"
    with open(latest_file, 'w') as f:
        json.dump(sightings, f, indent=2)


def generate_summary_stats(sightings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics from sightings.
    
    Args:
        sightings: List of sighting dictionaries
        
    Returns:
        Dictionary of statistics
    """
    stats = {
        'total_sightings': len(sightings),
        'by_species': {},
        'by_source': {},
        'by_gmu': {},
        'timestamp': datetime.now().isoformat()
    }
    
    for sighting in sightings:
        # Count by species
        species = sighting.get('species', 'unknown')
        stats['by_species'][species] = stats['by_species'].get(species, 0) + 1
        
        # Count by source
        source = sighting.get('source_type', 'unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        # Count by GMU
        gmu = sighting.get('gmu_unit', 'unmapped')
        stats['by_gmu'][gmu] = stats['by_gmu'].get(gmu, 0) + 1
    
    return stats


def main():
    """Run all scrapers and save results."""
    logger.info("=== Hunting Sightings Channel - Daily Scraper Run ===")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run scrapers
    sightings = run_all_scrapers(lookback_days=1)
    
    # Save results
    if sightings:
        save_sightings(sightings)
        
        # Generate and log statistics
        stats = generate_summary_stats(sightings)
        logger.info(f"\nSummary Statistics:")
        logger.info(f"Total sightings: {stats['total_sightings']}")
        logger.info(f"By species: {stats['by_species']}")
        logger.info(f"By source: {stats['by_source']}")
        logger.info(f"By GMU: {stats['by_gmu']}")
    else:
        logger.warning("No sightings found in this run")
    
    logger.info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
