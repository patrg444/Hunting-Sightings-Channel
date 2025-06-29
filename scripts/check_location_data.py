import requests
import json
from datetime import datetime

# Get all sightings
all_sightings = []
page = 1
while page <= 20:  # Limit to 20 pages for safety
    response = requests.get(f"http://localhost:8001/api/v1/sightings?page={page}&page_size=100")
    data = response.json()
    if not data.get('sightings'):
        break
    all_sightings.extend(data['sightings'])
    print(f"Fetched page {page}, got {len(data['sightings'])} sightings")
    if len(data['sightings']) < 100:
        break
    page += 1

print(f"Total sightings: {len(all_sightings)}")

# Group by date and check location data
by_date = {}
for s in all_sightings:
    date = s['created_at'].split('T')[0]
    if date not in by_date:
        by_date[date] = {'total': 0, 'with_location': 0, 'examples': []}
    
    by_date[date]['total'] += 1
    if s.get('location') is not None:
        by_date[date]['with_location'] += 1
        if len(by_date[date]['examples']) < 2:
            by_date[date]['examples'].append({
                'species': s.get('species'),
                'location_name': s.get('location_name'),
                'location': s.get('location')
            })

# Print summary
print("\nSightings by date:")
for date in sorted(by_date.keys()):
    info = by_date[date]
    print(f"{date}: {info['total']} total, {info['with_location']} with coordinates")
    if info['examples']:
        print(f"  Examples with coords: {info['examples']}")

# Check our new sightings specifically
print("\nChecking today's sightings (2025-06-28/29):")
today_sightings = [s for s in all_sightings if '2025-06-28' in s['created_at'] or '2025-06-29' in s['created_at']]
print(f"Found {len(today_sightings)} sightings from today")
print(f"With location coordinates: {len([s for s in today_sightings if s.get('location') is not None])}")
print(f"First few examples:")
for s in today_sightings[:3]:
    print(f"  - {s.get('species')} at {s.get('location_name')}, location: {s.get('location')}")