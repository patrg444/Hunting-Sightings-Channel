#!/usr/bin/env python3
"""
Debug why table isn't showing links.
"""

import requests
import json

# Make the same request the frontend should be making
response = requests.get("http://localhost:8002/api/v1/sightings", params={
    "page": 1,
    "page_size": 10,
    "start_date": "2025-06-24"
})

data = response.json()
print(f"Total sightings: {data['total']}")
print(f"Returned: {len(data['sightings'])}")
print("\nFirst 5 sightings:")
print("Date       | Species      | Source      | Has URL | Has Coords")
print("-----------|--------------|-------------|---------|------------")

for s in data['sightings'][:5]:
    date = s.get('sighting_date', 'Unknown')[:10]
    species = s.get('species', 'Unknown')[:12]
    source = s.get('source_type', 'Unknown')[:12]
    has_url = "Yes" if s.get('source_url') else "No"
    has_coords = "Yes" if (s.get('location') or (s.get('lat') and s.get('lng'))) else "No"
    
    print(f"{date:10} | {species:12} | {source:12} | {has_url:7} | {has_coords}")

# Check specifically for iNaturalist sightings
print("\n\niNaturalist sightings in response:")
inat_count = 0
for s in data['sightings']:
    if s.get('source_type') == 'inaturalist':
        inat_count += 1
        if inat_count <= 3:
            print(f"  {s['species']} on {s['sighting_date']} - URL: {s.get('source_url', 'NO URL')}")

print(f"\nTotal iNaturalist sightings in this page: {inat_count}")