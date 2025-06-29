#!/usr/bin/env python3
"""
Remove exact duplicates based on raw_text content.
More aggressive deduplication for sources with clear duplicates.
"""
import os
import sys
from datetime import datetime
from typing import List, Dict

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

def remove_exact_text_duplicates():
    """Remove exact text duplicates, keeping the oldest record."""
    logger.info("Finding exact text duplicates...")
    
    # First, get all duplicates grouped by raw_text
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
    
    logger.info(f"Loaded {len(all_sightings)} total sightings")
    
    # Group by raw_text
    text_groups = {}
    for sighting in all_sightings:
        text = sighting.get('raw_text', '')
        if text:  # Only process non-empty texts
            if text not in text_groups:
                text_groups[text] = []
            text_groups[text].append(sighting)
    
    # Find duplicates
    duplicate_groups = {
        text: sightings 
        for text, sightings in text_groups.items() 
        if len(sightings) > 1
    }
    
    logger.info(f"Found {len(duplicate_groups)} groups with exact text duplicates")
    
    # Process each duplicate group
    total_deleted = 0
    deletion_log = []
    
    for text, sightings in duplicate_groups.items():
        # Sort by created_at to keep oldest
        sightings.sort(key=lambda x: x.get('created_at', ''))
        
        # Log the group
        logger.info(f"\nProcessing {len(sightings)} duplicates from {sightings[0]['source_type']}")
        logger.debug(f"Text preview: {text[:100]}...")
        
        # Keep the first (oldest) and delete the rest
        keep = sightings[0]
        to_delete = sightings[1:]
        
        for sighting in to_delete:
            try:
                response = supabase.table('sightings') \
                    .delete() \
                    .eq('id', sighting['id']) \
                    .execute()
                
                if response.data:
                    total_deleted += 1
                    deletion_log.append({
                        'deleted_id': sighting['id'],
                        'kept_id': keep['id'],
                        'source': sighting['source_type'],
                        'date': sighting.get('sighting_date'),
                        'species': sighting.get('species')
                    })
                    logger.debug(f"  Deleted duplicate {sighting['id']}")
                    
            except Exception as e:
                logger.error(f"  Failed to delete {sighting['id']}: {e}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("EXACT DUPLICATE REMOVAL COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total duplicate groups: {len(duplicate_groups)}")
    logger.info(f"Total duplicates deleted: {total_deleted}")
    
    # Save deletion log
    if deletion_log:
        import json
        log_file = f"exact_duplicate_removal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'groups_processed': len(duplicate_groups),
                'records_deleted': total_deleted,
                'deletions': deletion_log
            }, f, indent=2)
        logger.info(f"\nDeletion log saved to: {log_file}")

def remove_null_text_duplicates():
    """Remove duplicates with null/empty text from same source and date."""
    logger.info("\nRemoving null text duplicates...")
    
    # Get all records with null/empty text
    response = supabase.table('sightings') \
        .select("*") \
        .or_('raw_text.is.null,raw_text.eq.') \
        .order('created_at', desc=False) \
        .execute()
    
    null_text_sightings = response.data
    logger.info(f"Found {len(null_text_sightings)} sightings with null/empty text")
    
    # Group by source, species, and date
    groups = {}
    for sighting in null_text_sightings:
        key = f"{sighting.get('source_type')}|{sighting.get('species')}|{sighting.get('sighting_date')}"
        if key not in groups:
            groups[key] = []
        groups[key].append(sighting)
    
    # Process duplicates
    total_deleted = 0
    for key, sightings in groups.items():
        if len(sightings) > 1:
            # Sort by created_at, keep oldest
            sightings.sort(key=lambda x: x.get('created_at', ''))
            
            source, species, date = key.split('|')
            logger.info(f"\nProcessing {len(sightings)} null-text duplicates: {species} from {source} on {date}")
            
            # Keep first, delete rest
            for sighting in sightings[1:]:
                try:
                    response = supabase.table('sightings') \
                        .delete() \
                        .eq('id', sighting['id']) \
                        .execute()
                    
                    if response.data:
                        total_deleted += 1
                        logger.debug(f"  Deleted null-text duplicate {sighting['id']}")
                        
                except Exception as e:
                    logger.error(f"  Failed to delete {sighting['id']}: {e}")
    
    logger.info(f"\nNull-text duplicates deleted: {total_deleted}")
    return total_deleted

def main():
    """Main deduplication process."""
    logger.info("Starting aggressive deduplication process...")
    
    # Remove exact text duplicates
    remove_exact_text_duplicates()
    
    # Remove null text duplicates
    remove_null_text_duplicates()
    
    # Update content hashes for remaining records
    logger.info("\nEnsuring all records have content hashes...")
    
    response = supabase.table('sightings') \
        .select("id,species,location_name,sighting_date,source_type") \
        .is_('content_hash', 'null') \
        .execute()
    
    if response.data:
        logger.info(f"Adding content hashes to {len(response.data)} records...")
        
        import hashlib
        for sighting in response.data:
            # Generate hash
            species = (sighting.get('species') or '').lower().strip()
            location = (sighting.get('location_name') or '').lower().strip()
            date = str(sighting.get('sighting_date', ''))
            source = (sighting.get('source_type') or '').lower().strip()
            
            content = f"{species}_{location}_{date}_{source}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            try:
                supabase.table('sightings') \
                    .update({'content_hash': content_hash}) \
                    .eq('id', sighting['id']) \
                    .execute()
            except Exception as e:
                logger.error(f"Failed to add hash to {sighting['id']}: {e}")
        
        logger.success("Content hashes updated")
    
    logger.success("\nAggressive deduplication complete!")

if __name__ == "__main__":
    main()