#!/usr/bin/env python3
"""
Merge duplicate sightings in the database.
Identifies duplicates based on species, location, date, and source.
"""
import os
import sys
import hashlib
from datetime import datetime
from typing import List, Dict, Set
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
from loguru import logger

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def generate_content_hash(sighting: Dict) -> str:
    """Generate consistent content hash for deduplication."""
    # Use species, location_name, and date for hash
    species = (sighting.get('species') or '').lower().strip()
    location = (sighting.get('location_name') or '').lower().strip()
    date = str(sighting.get('sighting_date', ''))
    source = (sighting.get('source_type') or '').lower().strip()
    
    content = f"{species}_{location}_{date}_{source}"
    return hashlib.md5(content.encode()).hexdigest()

def get_location_key(sighting: Dict) -> str:
    """Get location key for grouping similar locations."""
    # Try to use coordinates if available
    if sighting.get('location'):
        # Parse PostGIS point format: POINT(lng lat)
        try:
            point = sighting['location']
            if point and 'POINT' in point:
                coords = point.replace('POINT(', '').replace(')', '').split()
                if len(coords) == 2:
                    lng, lat = float(coords[0]), float(coords[1])
                    # Round to 3 decimal places (about 100m precision)
                    return f"{lat:.3f},{lng:.3f}"
        except:
            pass
    
    # Fallback to location name
    location_name = sighting.get('location_name', 'unknown')
    if location_name is None:
        location_name = 'unknown'
    return location_name.lower().strip()

def find_duplicate_groups() -> Dict[str, List[Dict]]:
    """Find groups of duplicate sightings."""
    logger.info("Fetching all sightings from database...")
    
    # Fetch all sightings
    all_sightings = []
    offset = 0
    
    while True:
        response = supabase.table('sightings') \
            .select("*") \
            .order('created_at', desc=False) \
            .range(offset, offset + 999) \
            .execute()
        
        if not response.data:
            break
            
        all_sightings.extend(response.data)
        offset += 1000
    
    logger.info(f"Found {len(all_sightings)} total sightings")
    
    # Group by potential duplicate key
    duplicate_groups = defaultdict(list)
    
    for sighting in all_sightings:
        # Create a key for grouping potential duplicates
        species = sighting.get('species', '').lower().strip()
        location_key = get_location_key(sighting)
        date = str(sighting.get('sighting_date', ''))
        
        # Group by species, location, and date
        group_key = f"{species}|{location_key}|{date}"
        duplicate_groups[group_key].append(sighting)
    
    # Filter to only groups with duplicates
    actual_duplicates = {
        key: sightings 
        for key, sightings in duplicate_groups.items() 
        if len(sightings) > 1
    }
    
    logger.info(f"Found {len(actual_duplicates)} groups with potential duplicates")
    
    return actual_duplicates

def merge_sighting_data(sightings: List[Dict]) -> Dict:
    """Merge multiple duplicate sightings into one comprehensive record."""
    # Start with the oldest sighting as base
    merged = sightings[0].copy()
    
    # Track which fields have been updated
    updates = set()
    
    for sighting in sightings[1:]:
        # Merge coordinates (prefer non-null)
        if not merged.get('location') and sighting.get('location'):
            merged['location'] = sighting['location']
            updates.add('location')
        
        # Merge location confidence radius (prefer smaller/more specific)
        if sighting.get('location_confidence_radius'):
            current_radius = merged.get('location_confidence_radius')
            new_radius = sighting['location_confidence_radius']
            if not current_radius or new_radius < current_radius:
                merged['location_confidence_radius'] = new_radius
                updates.add('location_confidence_radius')
        
        # Merge description (prefer longer)
        if sighting.get('description'):
            current_desc = merged.get('description', '')
            new_desc = sighting['description']
            if len(new_desc) > len(current_desc or ''):
                merged['description'] = new_desc
                updates.add('description')
        
        # Merge raw_text (prefer longer)
        if sighting.get('raw_text'):
            current_text = merged.get('raw_text', '')
            new_text = sighting['raw_text']
            if len(new_text) > len(current_text or ''):
                merged['raw_text'] = new_text
                updates.add('raw_text')
        
        # Keep highest confidence score
        if sighting.get('confidence_score'):
            current_conf = merged.get('confidence_score', 0)
            new_conf = sighting['confidence_score']
            if new_conf > current_conf:
                merged['confidence_score'] = new_conf
                updates.add('confidence_score')
        
        # Combine source URLs
        if sighting.get('source_url'):
            current_url = merged.get('source_url', '')
            new_url = sighting['source_url']
            if new_url not in current_url:
                if current_url:
                    merged['source_url'] = f"{current_url}; {new_url}"
                else:
                    merged['source_url'] = new_url
                updates.add('source_url')
    
    # Update content hash
    merged['content_hash'] = generate_content_hash(merged)
    
    # Update timestamps
    merged['updated_at'] = datetime.now().isoformat()
    
    return merged, updates

def main():
    """Main deduplication process."""
    logger.info("Starting sighting deduplication process...")
    
    # Find duplicate groups
    duplicate_groups = find_duplicate_groups()
    
    if not duplicate_groups:
        logger.info("No duplicates found!")
        return
    
    # Process each duplicate group
    total_deleted = 0
    total_merged = 0
    merge_log = []
    
    for group_key, sightings in duplicate_groups.items():
        if len(sightings) < 2:
            continue
        
        # Sort by created_at to keep oldest
        sightings.sort(key=lambda x: x.get('created_at', ''))
        
        # Log the group
        species, location, date = group_key.split('|')
        logger.info(f"\nProcessing {len(sightings)} duplicates: {species} at {location} on {date}")
        
        # Check if they're truly duplicates or just similar
        unique_sources = set(s.get('source_type') for s in sightings)
        
        if len(unique_sources) > 1:
            # Different sources - might be legitimate different sightings
            logger.warning(f"  Multiple sources found: {unique_sources} - skipping merge")
            continue
        
        # Merge the sightings
        merged_sighting, updated_fields = merge_sighting_data(sightings)
        
        # Keep the first (oldest) sighting and update it
        keep_id = sightings[0]['id']
        delete_ids = [s['id'] for s in sightings[1:]]
        
        # Update the keeper with merged data
        try:
            # Remove fields that can't be updated
            update_data = merged_sighting.copy()
            for field in ['id', 'created_at']:
                update_data.pop(field, None)
            
            response = supabase.table('sightings') \
                .update(update_data) \
                .eq('id', keep_id) \
                .execute()
            
            if response.data:
                logger.success(f"  Updated sighting {keep_id} with fields: {updated_fields}")
                total_merged += 1
                
                # Delete the duplicates
                for delete_id in delete_ids:
                    del_response = supabase.table('sightings') \
                        .delete() \
                        .eq('id', delete_id) \
                        .execute()
                    
                    if del_response.data:
                        total_deleted += 1
                        logger.debug(f"  Deleted duplicate {delete_id}")
                
                merge_log.append({
                    'group': group_key,
                    'kept_id': keep_id,
                    'deleted_ids': delete_ids,
                    'updated_fields': list(updated_fields),
                    'sources': list(unique_sources)
                })
                
        except Exception as e:
            logger.error(f"  Failed to merge group: {e}")
    
    # Generate summary report
    logger.info(f"\n{'='*60}")
    logger.info("DEDUPLICATION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total groups processed: {len(duplicate_groups)}")
    logger.info(f"Sightings merged: {total_merged}")
    logger.info(f"Duplicates deleted: {total_deleted}")
    
    # Save merge log
    if merge_log:
        import json
        log_file = f"merge_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_groups': len(duplicate_groups),
                'merged': total_merged,
                'deleted': total_deleted,
                'merges': merge_log
            }, f, indent=2)
        logger.info(f"\nMerge log saved to: {log_file}")
    
    # Add content hashes for records that don't have them
    logger.info("\nAdding content hashes to records without them...")
    
    no_hash_response = supabase.table('sightings') \
        .select("id,species,location_name,sighting_date,source_type") \
        .is_('content_hash', 'null') \
        .execute()
    
    if no_hash_response.data:
        logger.info(f"Found {len(no_hash_response.data)} sightings without content hash")
        
        for sighting in no_hash_response.data:
            content_hash = generate_content_hash(sighting)
            
            try:
                supabase.table('sightings') \
                    .update({'content_hash': content_hash}) \
                    .eq('id', sighting['id']) \
                    .execute()
            except Exception as e:
                logger.error(f"Failed to add hash to {sighting['id']}: {e}")
        
        logger.success("Content hashes added")

if __name__ == "__main__":
    main()