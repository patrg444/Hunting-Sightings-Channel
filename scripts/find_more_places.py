#!/usr/bin/env python3
"""Find more Google Place IDs to reach target of ~90 locations"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict
import time

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

# Additional high-traffic locations we haven't tried yet
MORE_LOCATIONS = [
    # Specific passes with better search terms
    {"name": "Rabbit Ears Pass", "search": "Rabbit Ears Pass Rest Area Colorado", "gmu_hint": 14, "type": "scenic"},
    {"name": "Vail Pass", "search": "Vail Pass Rest Area Colorado", "gmu_hint": 36, "type": "scenic"},
    {"name": "Loveland Pass", "search": "Loveland Pass Summit Colorado", "gmu_hint": 39, "type": "scenic"},
    {"name": "Wolf Creek Pass", "search": "Wolf Creek Pass Summit Colorado", "gmu_hint": 76, "type": "scenic"},
    {"name": "Hoosier Pass", "search": "Hoosier Pass Summit Alma Colorado", "gmu_hint": 47, "type": "scenic"},
    
    # More State Parks and scenic areas from the suggestions
    {"name": "Barr Lake State Park", "search": "Barr Lake State Park Brighton Colorado", "gmu_hint": 95, "type": "state_park"},
    {"name": "Navajo State Park", "search": "Navajo State Park Arboles Colorado", "gmu_hint": 73, "type": "state_park"},
    {"name": "Lake Pueblo State Park", "search": "Lake Pueblo State Park Colorado", "gmu_hint": 119, "type": "state_park"},
    
    # Popular fishing/recreation areas
    {"name": "Blue Mesa Reservoir", "search": "Blue Mesa Reservoir Gunnison Colorado", "gmu_hint": 551, "type": "lake"},
    {"name": "Vallecito Lake", "search": "Vallecito Lake Bayfield Colorado", "gmu_hint": 74, "type": "lake"},
    {"name": "Twin Lakes", "search": "Twin Lakes Colorado Leadville", "gmu_hint": 48, "type": "lake"},
    
    # More campgrounds in popular areas
    {"name": "Turquoise Lake", "search": "Turquoise Lake Leadville Colorado", "gmu_hint": 48, "type": "lake"},
    {"name": "Clear Creek Reservoir", "search": "Clear Creek Reservoir Georgetown Colorado", "gmu_hint": 39, "type": "lake"},
]

def find_place_id(location: Dict, api_key: str) -> Dict:
    """Find Google Place ID for a location using Places API text search"""
    
    search_query = location.get('search', location['name'])
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        'query': search_query,
        'key': api_key,
        'region': 'us'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            # Get the first result
            place = data['results'][0]
            
            # Get place details
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                'place_id': place['place_id'],
                'fields': 'name,formatted_address,rating,user_ratings_total,types',
                'key': api_key
            }
            
            details_response = requests.get(details_url, params=details_params)
            details_data = details_response.json()
            
            if details_data.get('status') == 'OK':
                result = details_data.get('result', {})
                
                # Check if it's in Colorado
                if 'CO' in result.get('formatted_address', '') or 'Colorado' in result.get('formatted_address', ''):
                    return {
                        'place_id': place['place_id'],
                        'name': result.get('name', ''),
                        'formatted_address': result.get('formatted_address', ''),
                        'rating': result.get('rating', 0),
                        'total_ratings': result.get('user_ratings_total', 0),
                        'types': result.get('types', []),
                        'found': True
                    }
                else:
                    return {'found': False, 'query': search_query, 'error': f"Not in Colorado: {result.get('formatted_address', '')}"}
        
        return {'found': False, 'query': search_query, 'error': f"No results found (Status: {data.get('status')})"}
        
    except Exception as e:
        return {'found': False, 'query': search_query, 'error': str(e)}

def main():
    if not GOOGLE_PLACES_API_KEY:
        print("Error: GOOGLE_PLACES_API_KEY not found in .env file")
        return
    
    print(f"Finding Place IDs for {len(MORE_LOCATIONS)} more locations...")
    print("=" * 80)
    
    results = []
    found_count = 0
    
    for idx, location in enumerate(MORE_LOCATIONS, 1):
        print(f"\n[{idx}/{len(MORE_LOCATIONS)}] Searching for: {location['name']}")
        print(f"  Query: {location.get('search', location['name'])}")
        
        result = find_place_id(location, GOOGLE_PLACES_API_KEY)
        
        if result['found']:
            found_count += 1
            print(f"✓ Found: {result['name']}")
            print(f"  Place ID: {result['place_id']}")
            print(f"  Ratings: {result['total_ratings']}")
            
            # Add to results with original metadata
            results.append({
                'place_id': result['place_id'],
                'name': result['name'],
                'total_ratings': result['total_ratings'],
                'gmu_hint': location['gmu_hint'],
                'type': location['type']
            })
        else:
            print(f"✗ Not found: {location['name']}")
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    print("\n" + "=" * 80)
    print(f"Found {found_count} out of {len(MORE_LOCATIONS)} locations")
    
    # Save results
    output_file = '/Users/patrickgloria/Hunting-Sightings-Channel/data/more_google_places.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total_searched': len(MORE_LOCATIONS),
            'total_found': found_count,
            'places': sorted(results, key=lambda x: x['total_ratings'], reverse=True)
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Show summary
    if results:
        print("\nFound places (sorted by rating count):")
        for place in sorted(results, key=lambda x: x['total_ratings'], reverse=True):
            print(f"  - {place['name']} ({place['total_ratings']} ratings) - GMU {place['gmu_hint']}")

if __name__ == "__main__":
    main()