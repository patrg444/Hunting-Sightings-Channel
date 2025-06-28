#!/usr/bin/env python3
"""
Helper script to find Google Place IDs for Colorado locations.
"""

import os
import sys
import requests
import json
from loguru import logger
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
try:
    from dotenv import load_dotenv
    # Try multiple .env locations
    env_paths = [
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent / '.env.client'
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from: {env_path}")
            break
except ImportError:
    logger.warning("python-dotenv not installed")

def find_place_id(place_name, api_key):
    """Find Google Place ID for a location."""
    base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    
    params = {
        'input': f"{place_name} Colorado",
        'inputtype': 'textquery',
        'fields': 'place_id,name,formatted_address,user_ratings_total,geometry',
        'key': api_key
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if data.get('candidates'):
        candidate = data['candidates'][0]
        return {
            'place_id': candidate.get('place_id'),
            'name': candidate.get('name'),
            'address': candidate.get('formatted_address'),
            'total_ratings': candidate.get('user_ratings_total', 0),
            'lat': candidate.get('geometry', {}).get('location', {}).get('lat'),
            'lng': candidate.get('geometry', {}).get('location', {}).get('lng')
        }
    return None

def main():
    """Find Place IDs for suggested locations."""
    
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        logger.error("GOOGLE_PLACES_API_KEY not set!")
        return
    
    # Top priority locations to add
    locations_to_find = [
        # National Parks & Monuments
        ("Black Canyon of the Gunnison National Park", 62),
        ("Great Sand Dunes National Park", 68),
        ("Mesa Verde National Park", 73),
        ("Colorado National Monument", 40),
        ("Dinosaur National Monument", 10),
        
        # Popular State Parks
        ("Cherry Creek State Park", 39),
        ("Chatfield State Park", 39),
        ("Boyd Lake State Park", 95),
        ("Eleven Mile State Park", 50),
        ("Spinney Mountain State Park", 50),
        ("Ridgway State Park", 62),
        ("Sylvan Lake State Park", 36),
        ("Stagecoach State Park", 14),
        
        # Popular Areas
        ("Garden of the Gods", 58),
        ("Brainard Lake Recreation Area", 20),
        ("Mount Evans Scenic Byway", 39),
        ("Pikes Peak Highway", 58),
        ("Trail Ridge Road", 20),
        
        # Wildlife Areas
        ("Georgetown Wildlife Viewing Area", 39),
        ("Genesee Park Buffalo Herd", 39),
        ("Rocky Mountain Arsenal Wildlife Refuge", 95),
    ]
    
    results = []
    
    logger.info(f"Finding Place IDs for {len(locations_to_find)} locations...")
    
    for location_name, gmu_hint in locations_to_find:
        logger.info(f"\nSearching for: {location_name}")
        place_info = find_place_id(location_name, api_key)
        
        if place_info:
            place_info['gmu_hint'] = gmu_hint
            results.append(place_info)
            logger.success(f"✓ Found: {place_info['name']}")
            logger.info(f"  Place ID: {place_info['place_id']}")
            logger.info(f"  Ratings: {place_info['total_ratings']}")
            logger.info(f"  GMU: {gmu_hint}")
        else:
            logger.warning(f"✗ Not found: {location_name}")
    
    # Save results
    output_file = "data/new_google_places.json"
    with open(output_file, 'w') as f:
        json.dump({
            'new_places': results,
            'total_found': len(results)
        }, f, indent=2)
    
    logger.success(f"\nFound {len(results)} places. Saved to {output_file}")
    
    # Show summary
    high_traffic = [p for p in results if p['total_ratings'] > 1000]
    logger.info(f"\nHigh-traffic locations (>1000 reviews): {len(high_traffic)}")
    for place in sorted(high_traffic, key=lambda x: x['total_ratings'], reverse=True)[:5]:
        logger.info(f"  - {place['name']}: {place['total_ratings']} reviews")

if __name__ == "__main__":
    main()