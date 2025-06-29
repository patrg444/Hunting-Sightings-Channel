import json

try:
    with open('/Users/patrickgloria/Hunting-Sightings-Channel/data/cache/parsed_posts.json', 'r') as f:
        cache = json.load(f)
    
    # Count cache entries and sightings
    total_entries = len(cache)
    total_sightings_listed = 0
    inconsistent_entries = 0
    
    for post_id, data in cache.items():
        sighting_count = data.get('sighting_count', 0)
        actual_sightings = len(data.get('sightings', []))
        total_sightings_listed += actual_sightings
        
        if sighting_count != actual_sightings:
            inconsistent_entries += 1
            if inconsistent_entries <= 5:  # Show first 5 examples
                print(f'Inconsistent: {post_id} - counted: {sighting_count}, actual: {actual_sightings}')
    
    print(f'\nTotal cache entries: {total_entries}')
    print(f'Total sightings in arrays: {total_sightings_listed}')
    print(f'Inconsistent entries: {inconsistent_entries}')
    
except json.JSONDecodeError as e:
    print(f'JSON decode error: {e}')
except Exception as e:
    print(f'Error: {e}')