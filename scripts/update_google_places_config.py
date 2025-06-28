#!/usr/bin/env python3
"""
Script to merge new Google Places into the existing config.
"""

import json
from pathlib import Path
from loguru import logger

def update_config():
    """Merge new places into existing config."""
    
    # Load existing config
    config_path = Path(__file__).parent.parent / "data" / "google_places_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load new places
    new_places_path = Path(__file__).parent.parent / "data" / "new_google_places.json"
    with open(new_places_path, 'r') as f:
        new_data = json.load(f)
    
    # Get existing place IDs to avoid duplicates
    existing_ids = {place['place_id'] for place in config['trails']}
    
    # Add new places that aren't already in config
    added_count = 0
    for place in new_data['new_places']:
        if place['place_id'] not in existing_ids:
            # Format to match existing structure
            trail_entry = {
                "place_id": place['place_id'],
                "name": place['name'],
                "total_ratings": place['total_ratings'],
                "gmu_hint": place['gmu_hint']
            }
            
            # Add type if we can determine it
            if "National Park" in place['name']:
                trail_entry['type'] = "national_park"
            elif "State Park" in place['name']:
                trail_entry['type'] = "state_park"
            elif "Wildlife" in place['name']:
                trail_entry['type'] = "wildlife"
            elif "Monument" in place['name']:
                trail_entry['type'] = "monument"
            
            config['trails'].append(trail_entry)
            added_count += 1
            logger.info(f"Added: {place['name']} ({place['total_ratings']} reviews)")
    
    # Sort by total_ratings descending
    config['trails'].sort(key=lambda x: x['total_ratings'], reverse=True)
    
    # Update max_trails_per_run if needed
    if len(config['trails']) > 80:
        config['max_trails_per_run'] = 90
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.success(f"\nAdded {added_count} new locations")
    logger.info(f"Total locations now: {len(config['trails'])}")
    
    # Show top 10 by ratings
    logger.info("\nTop 10 locations by ratings:")
    for i, trail in enumerate(config['trails'][:10], 1):
        logger.info(f"{i}. {trail['name']}: {trail['total_ratings']} reviews")

if __name__ == "__main__":
    update_config()