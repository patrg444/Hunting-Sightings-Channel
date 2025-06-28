#!/usr/bin/env python3
"""Update Google Places configuration with all found locations"""

import json
from typing import List, Dict

def load_existing_config():
    """Load the existing Google Places configuration"""
    with open('/Users/patrickgloria/Hunting-Sightings-Channel/data/google_places_config.json', 'r') as f:
        return json.load(f)

def load_additional_places():
    """Load the additional places we found"""
    additional_places = []
    
    # Load first batch of additional places
    try:
        with open('/Users/patrickgloria/Hunting-Sightings-Channel/data/additional_google_places.json', 'r') as f:
            data = json.load(f)
            # Filter out places with 0 ratings or that are just roads
            for place in data['places']:
                if place['total_ratings'] > 0 and 'Road' not in place['name'] and place['name'] not in ['Colorado 14', 'Colorado 9']:
                    additional_places.append({
                        'place_id': place['place_id'],
                        'name': place['name'],
                        'total_ratings': place['total_ratings'],
                        'gmu_hint': place['gmu_hint'],
                        'type': place['type']
                    })
    except FileNotFoundError:
        print("Warning: additional_google_places.json not found")
    
    # Load second batch of additional places
    try:
        with open('/Users/patrickgloria/Hunting-Sightings-Channel/data/more_google_places.json', 'r') as f:
            data = json.load(f)
            for place in data['places']:
                additional_places.append({
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'total_ratings': place['total_ratings'],
                    'gmu_hint': place['gmu_hint'],
                    'type': place['type']
                })
    except FileNotFoundError:
        print("Warning: more_google_places.json not found")
    
    return additional_places

def merge_places(existing_trails: List[Dict], new_places: List[Dict]) -> List[Dict]:
    """Merge existing and new places, avoiding duplicates"""
    # Create a set of existing place IDs
    existing_ids = {trail['place_id'] for trail in existing_trails}
    
    # Add new places that aren't duplicates
    for place in new_places:
        if place['place_id'] not in existing_ids:
            existing_trails.append(place)
            existing_ids.add(place['place_id'])
    
    # Sort by total_ratings descending
    return sorted(existing_trails, key=lambda x: x['total_ratings'], reverse=True)

def main():
    # Load existing configuration
    config = load_existing_config()
    existing_trails = config['trails']
    
    print(f"Current number of places: {len(existing_trails)}")
    
    # Load additional places
    additional_places = load_additional_places()
    print(f"Found {len(additional_places)} additional places to add")
    
    # Merge places
    all_places = merge_places(existing_trails, additional_places)
    
    print(f"Total places after merge: {len(all_places)}")
    
    # Update configuration
    config['trails'] = all_places
    config['comment'] = f"Verified Colorado trail place IDs for wildlife sighting extraction - {len(all_places)} locations total"
    
    # Save updated configuration
    output_file = '/Users/patrickgloria/Hunting-Sightings-Channel/data/google_places_config_updated.json'
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nUpdated configuration saved to: {output_file}")
    print(f"Total locations: {len(all_places)}")
    
    # Show summary statistics
    print("\nLocation type breakdown:")
    type_counts = {}
    for place in all_places:
        place_type = place.get('type', 'unknown')
        type_counts[place_type] = type_counts.get(place_type, 0) + 1
    
    for place_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {place_type}: {count}")
    
    print("\nTop 10 locations by rating count:")
    for i, place in enumerate(all_places[:10], 1):
        print(f"  {i}. {place['name']} ({place['total_ratings']} ratings)")

if __name__ == "__main__":
    main()