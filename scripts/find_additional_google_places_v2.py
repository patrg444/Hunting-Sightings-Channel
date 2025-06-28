#!/usr/bin/env python3
"""Find additional Google Place IDs for Colorado locations - improved version"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict
import time

# Load environment variables
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

# Additional locations to find based on suggested_google_places_additions.md
# Using more specific search terms
ADDITIONAL_LOCATIONS = [
    # Wildlife Refuges (use more specific names)
    {"name": "Arapaho National Wildlife Refuge", "search": "Arapaho National Wildlife Refuge Walden Colorado", "gmu_hint": 17, "type": "wildlife"},
    {"name": "Monte Vista National Wildlife Refuge", "search": "Monte Vista National Wildlife Refuge Colorado", "gmu_hint": 68, "type": "wildlife"},
    {"name": "Browns Park National Wildlife Refuge", "search": "Browns Park National Wildlife Refuge Maybell Colorado", "gmu_hint": 2, "type": "wildlife"},
    
    # Popular Passes (remove "Pass" for better results)
    {"name": "Rabbit Ears Pass", "search": "Rabbit Ears Pass Colorado Highway 40", "gmu_hint": 14, "type": "scenic"},
    {"name": "Vail Pass", "search": "Vail Pass Colorado I-70", "gmu_hint": 36, "type": "scenic"},
    {"name": "Loveland Pass", "search": "Loveland Pass Colorado US 6", "gmu_hint": 39, "type": "scenic"},
    {"name": "Cameron Pass", "search": "Cameron Pass Colorado State Highway 14", "gmu_hint": 14, "type": "scenic"},
    {"name": "Wolf Creek Pass", "search": "Wolf Creek Pass Colorado US 160", "gmu_hint": 76, "type": "scenic"},
    {"name": "Hoosier Pass", "search": "Hoosier Pass Colorado Highway 9", "gmu_hint": 47, "type": "scenic"},
    {"name": "Tennessee Pass", "search": "Tennessee Pass Colorado Leadville", "gmu_hint": 48, "type": "scenic"},
    {"name": "La Veta Pass", "search": "La Veta Pass Colorado US 160", "gmu_hint": 83, "type": "scenic"},
    
    # High-traffic parks
    {"name": "Red Rocks Park and Amphitheatre", "search": "Red Rocks Amphitheatre Morrison Colorado", "gmu_hint": 39, "type": "park"},
    {"name": "Chautauqua Park", "search": "Chautauqua Park Boulder Colorado", "gmu_hint": 38, "type": "park"},
    {"name": "Bear Creek Lake Park", "search": "Bear Creek Lake Park Lakewood Colorado", "gmu_hint": 39, "type": "park"},
    {"name": "Lair o' the Bear Park", "search": "Lair o the Bear Park Jefferson County Colorado", "gmu_hint": 39, "type": "park"},
    
    # Popular trailheads (simplify names)
    {"name": "Ice Lake Basin", "search": "Ice Lake Basin Silverton Colorado", "gmu_hint": 74, "type": "trailhead"},
    {"name": "American Basin", "search": "American Basin Lake City Colorado", "gmu_hint": 76, "type": "trailhead"},
    {"name": "Cathedral Lake", "search": "Cathedral Lake Aspen Colorado", "gmu_hint": 49, "type": "trailhead"},
    {"name": "Conundrum Hot Springs", "search": "Conundrum Hot Springs Aspen Colorado", "gmu_hint": 49, "type": "trailhead"},
    
    # Additional state parks
    {"name": "Rifle Gap State Park", "search": "Rifle Gap State Park Colorado", "gmu_hint": 33, "type": "state_park"},
    {"name": "Pearl Lake State Park", "search": "Pearl Lake State Park Steamboat Springs Colorado", "gmu_hint": 14, "type": "state_park"},
    
    # Additional areas
    {"name": "Georgetown Lake", "search": "Georgetown Lake Colorado", "gmu_hint": 39, "type": "wildlife"},
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
        
        # Check API status
        if data.get('status') == 'REQUEST_DENIED':
            return {'found': False, 'query': search_query, 'error': f"API Error: {data.get('error_message', 'Request denied')}"}
        
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
    
    print(f"Finding Place IDs for {len(ADDITIONAL_LOCATIONS)} additional locations...")
    print(f"Using API key: {GOOGLE_PLACES_API_KEY[:10]}...")
    print("=" * 80)
    
    results = []
    found_count = 0
    
    for idx, location in enumerate(ADDITIONAL_LOCATIONS, 1):
        print(f"\n[{idx}/{len(ADDITIONAL_LOCATIONS)}] Searching for: {location['name']}")
        print(f"  Query: {location.get('search', location['name'])}")
        
        result = find_place_id(location, GOOGLE_PLACES_API_KEY)
        
        if result['found']:
            found_count += 1
            print(f"✓ Found: {result['name']}")
            print(f"  Place ID: {result['place_id']}")
            print(f"  Address: {result['formatted_address']}")
            print(f"  Ratings: {result['total_ratings']} (avg: {result.get('rating', 'N/A')})")
            print(f"  Types: {', '.join(result.get('types', []))}")
            
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
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
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
    if results:
        print("\nFound places (sorted by rating count):")
        for place in sorted(results, key=lambda x: x['total_ratings'], reverse=True):
            print(f"  - {place['name']} ({place['total_ratings']} ratings) - GMU {place['gmu_hint']}")

if __name__ == "__main__":
    main()