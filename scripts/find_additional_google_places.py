#!/usr/bin/env python3
"""Find additional Google Place IDs for Colorado locations"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

# Additional locations to find based on suggested_google_places_additions.md
# Focusing on categories not yet fully covered
ADDITIONAL_LOCATIONS = [
    # Wildlife Refuges
    {"name": "Arapaho National Wildlife Refuge", "gmu_hint": 17, "type": "wildlife"},
    {"name": "Monte Vista National Wildlife Refuge", "gmu_hint": 68, "type": "wildlife"},
    {"name": "Browns Park National Wildlife Refuge", "gmu_hint": 2, "type": "wildlife"},
    
    # Popular Passes (high-traffic scenic areas)
    {"name": "Rabbit Ears Pass", "gmu_hint": 14, "type": "scenic"},
    {"name": "Vail Pass Recreation Area", "gmu_hint": 36, "type": "scenic"},
    {"name": "Loveland Pass", "gmu_hint": 39, "type": "scenic"},
    {"name": "Cameron Pass", "gmu_hint": 14, "type": "scenic"},
    {"name": "Wolf Creek Pass", "gmu_hint": 76, "type": "scenic"},
    {"name": "Hoosier Pass", "gmu_hint": 47, "type": "scenic"},
    {"name": "Tennessee Pass", "gmu_hint": 48, "type": "scenic"},
    {"name": "La Veta Pass", "gmu_hint": 83, "type": "scenic"},
    
    # High-traffic parks not yet included
    {"name": "Red Rocks Park and Amphitheatre", "gmu_hint": 39, "type": "park"},
    {"name": "Chautauqua Park Boulder", "gmu_hint": 38, "type": "park"},
    {"name": "Bear Creek Lake Park", "gmu_hint": 39, "type": "park"},
    {"name": "Lair o' the Bear Park", "gmu_hint": 39, "type": "park"},
    
    # Popular trailheads
    {"name": "Ice Lake Trailhead Silverton", "gmu_hint": 74, "type": "trailhead"},
    {"name": "American Basin Trailhead", "gmu_hint": 76, "type": "trailhead"},
    {"name": "Cathedral Lake Trailhead", "gmu_hint": 49, "type": "trailhead"},
    {"name": "Conundrum Hot Springs Trailhead", "gmu_hint": 49, "type": "trailhead"},
    
    # Additional high-traffic state parks
    {"name": "Rifle Gap State Park", "gmu_hint": 33, "type": "state_park"},
    {"name": "Pearl Lake State Park", "gmu_hint": 14, "type": "state_park"},
    
    # Additional scenic/wildlife areas
    {"name": "Georgetown Wildlife Viewing Area", "gmu_hint": 39, "type": "wildlife"},
]

def find_place_id(location_name: str, api_key: str) -> Dict:
    """Find Google Place ID for a location using Places API text search"""
    
    # First try with exact name + Colorado
    search_query = f"{location_name} Colorado"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        'query': search_query,
        'key': api_key,
        'region': 'us',
        'type': 'park|point_of_interest|natural_feature|campground|tourist_attraction'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            # Get the first result
            place = data['results'][0]
            
            # Get place details to confirm it's in Colorado
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                'place_id': place['place_id'],
                'fields': 'name,formatted_address,rating,user_ratings_total',
                'key': api_key
            }
            
            details_response = requests.get(details_url, params=details_params)
            details_data = details_response.json()
            
            if details_data.get('status') == 'OK':
                result = details_data.get('result', {})
                
                # Check if it's in Colorado
                if 'Colorado' in result.get('formatted_address', ''):
                    return {
                        'place_id': place['place_id'],
                        'name': result.get('name', ''),
                        'formatted_address': result.get('formatted_address', ''),
                        'rating': result.get('rating', 0),
                        'total_ratings': result.get('user_ratings_total', 0),
                        'found': True
                    }
        
        return {'found': False, 'query': search_query, 'error': 'No results found'}
        
    except Exception as e:
        return {'found': False, 'query': search_query, 'error': str(e)}

def main():
    if not GOOGLE_PLACES_API_KEY:
        print("Error: GOOGLE_PLACES_API_KEY not found in .env file")
        return
    
    print(f"Finding Place IDs for {len(ADDITIONAL_LOCATIONS)} additional locations...")
    print("=" * 80)
    
    results = []
    found_count = 0
    
    for idx, location in enumerate(ADDITIONAL_LOCATIONS, 1):
        print(f"\n[{idx}/{len(ADDITIONAL_LOCATIONS)}] Searching for: {location['name']}")
        
        result = find_place_id(location['name'], GOOGLE_PLACES_API_KEY)
        
        if result['found']:
            found_count += 1
            print(f"✓ Found: {result['name']}")
            print(f"  Place ID: {result['place_id']}")
            print(f"  Address: {result['formatted_address']}")
            print(f"  Ratings: {result['total_ratings']} (avg: {result['rating']})")
            
            # Add to results with original metadata
            results.append({
                'place_id': result['place_id'],
                'name': result['name'],
                'total_ratings': result['total_ratings'],
                'gmu_hint': location['gmu_hint'],
                'type': location['type'],
                'original_search': location['name'],
                'formatted_address': result['formatted_address']
            })
        else:
            print(f"✗ Not found: {location['name']}")
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print(f"Found {found_count} out of {len(ADDITIONAL_LOCATIONS)} locations")
    
    # Save results
    output_file = '/Users/patrickgloria/Hunting-Sightings-Channel/data/additional_google_places.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total_searched': len(ADDITIONAL_LOCATIONS),
            'total_found': found_count,
            'places': sorted(results, key=lambda x: x['total_ratings'], reverse=True)
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Show summary of found places sorted by rating count
    print("\nFound places (sorted by rating count):")
    for place in sorted(results, key=lambda x: x['total_ratings'], reverse=True):
        print(f"  - {place['name']} ({place['total_ratings']} ratings) - GMU {place['gmu_hint']}")

if __name__ == "__main__":
    main()