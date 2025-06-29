import requests

# Check all sightings in batches
total = 794
offset = 0
batch_size = 100
sightings_with_location = 0
total_checked = 0

print("Checking all sightings for location data...")

while offset < total:
    response = requests.get(f"http://localhost:8001/api/v1/sightings?limit={batch_size}&offset={offset}")
    data = response.json()
    
    batch = data.get('sightings', [])
    if not batch:
        break
        
    for s in batch:
        total_checked += 1
        if s.get('location') is not None:
            sightings_with_location += 1
            print(f"Found sighting with location! {s.get('species')} at {s.get('location_name')}")
            print(f"  Location: {s.get('location')}")
            print(f"  Created: {s.get('created_at')}")
    
    print(f"Checked {offset + len(batch)}/{total} sightings...")
    offset += batch_size

print(f"\nSummary:")
print(f"Total sightings checked: {total_checked}")
print(f"Sightings with location coordinates: {sightings_with_location}")
print(f"Sightings without coordinates: {total_checked - sightings_with_location}")