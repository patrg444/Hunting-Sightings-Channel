import requests
import json

# Get recent sightings with coordinates
url = "http://localhost:8001/api/v1/sightings"
params = {"limit": 500, "offset": 250}
response = requests.get(url, params=params)
data = response.json()

sightings_with_coords = []
sightings_without_coords = []

for s in data['sightings']:
    if s.get('location'):
        sightings_with_coords.append({
            'species': s.get('species'),
            'location_name': s.get('location_name'),
            'created_at': s.get('created_at'),
            'radius': s.get('location_confidence_radius')
        })
    else:
        sightings_without_coords.append({
            'species': s.get('species'),
            'location_name': s.get('location_name'),
            'created_at': s.get('created_at'),
            'radius': s.get('location_confidence_radius')
        })

print(f"Found {len(sightings_with_coords)} sightings WITH coordinates")
print(f"Found {len(sightings_without_coords)} sightings WITHOUT coordinates")

if sightings_with_coords:
    print("\nFirst 5 with coordinates:")
    for s in sightings_with_coords[:5]:
        print(f"  - {s['species']} at {s['location_name']} (radius: {s['radius']} miles)")
        print(f"    Created: {s['created_at']}")

# Check date ranges
if sightings_with_coords:
    dates = [s['created_at'].split('T')[0] for s in sightings_with_coords]
    print(f"\nDate range of sightings with coords: {min(dates)} to {max(dates)}")

# Summary to help frontend
print("\n=== FRONTEND HELP ===")
print("To see sightings on the map, the frontend needs to:")
print("1. Either extend the date filter to include June 27 sightings (which have coordinates)")
print("2. Or we need to run the SQL script to add coordinates to recent sightings")
print("3. Current status: Recent sightings have radius values but no coordinates")