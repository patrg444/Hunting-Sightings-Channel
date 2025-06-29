#!/usr/bin/env python3
"""Check for duplicate entries via the API."""

import requests
from collections import defaultdict

API_URL = "http://localhost:8002/api/v1/sightings"

def check_duplicates():
    """Check for duplicate entries in the API response."""
    
    # Fetch elk sightings from June 27, 2025
    params = {
        "species_list": "elk",
        "sighting_date": "2025-06-27",
        "source_list": "14ers",
        "page_size": 50
    }
    
    response = requests.get(API_URL, params=params)
    data = response.json()
    
    print(f"Total entries found: {data['total']}")
    print(f"Fetched {len(data['items'])} items\n")
    
    # Group by raw_text and location_name
    groups = defaultdict(list)
    
    for item in data['items']:
        key = (
            item.get('raw_text', '')[:100],  # First 100 chars of text
            item.get('location_name', 'Unknown')
        )
        groups[key].append(item)
    
    # Find groups with duplicates
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    
    print(f"Found {len(duplicate_groups)} groups with duplicates:\n")
    
    total_duplicates = 0
    for (text, location), items in duplicate_groups.items():
        print(f"Location: {location}")
        print(f"Text: {text}...")
        print(f"Count: {len(items)} duplicates")
        print(f"IDs: {[item['id'] for item in items]}")
        print("-" * 80)
        total_duplicates += len(items) - 1
    
    print(f"\nTotal duplicate entries (extras to remove): {total_duplicates}")
    
    # Also check entries without location/text
    no_text = [item for item in data['items'] if not item.get('raw_text')]
    no_location = [item for item in data['items'] if not item.get('location_name')]
    
    print(f"\nEntries without raw_text: {len(no_text)}")
    print(f"Entries without location_name: {len(no_location)}")

if __name__ == "__main__":
    check_duplicates()