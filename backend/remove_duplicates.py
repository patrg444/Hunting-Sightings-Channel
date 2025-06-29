#!/usr/bin/env python3
"""
Script to identify and remove duplicate sightings from the database.
Duplicates are identified by having the same:
- species
- sighting_date
- source_type
- raw_text
- location_name
"""

import psycopg2
from datetime import datetime
import hashlib

DB_URL = "postgresql://patrickgloria:wildlifetracker2024@localhost:5432/wildlife_sightings_db"

def generate_content_hash(species, date, source, raw_text, location):
    """Generate a hash for deduplication."""
    content = f"{species}|{date}|{source}|{raw_text}|{location}"
    return hashlib.sha256(content.encode()).hexdigest()

def find_duplicates():
    """Find duplicate entries in the database."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    try:
        # Find groups of duplicates
        query = """
            SELECT 
                species, sighting_date, source_type, raw_text, location_name,
                COUNT(*) as duplicate_count,
                ARRAY_AGG(id ORDER BY created_at ASC) as ids,
                ARRAY_AGG(created_at ORDER BY created_at ASC) as created_dates
            FROM sightings
            WHERE content_hash IS NULL  -- Only look at entries without content hash
            GROUP BY species, sighting_date, source_type, raw_text, location_name
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC, sighting_date DESC
        """
        
        cursor.execute(query)
        duplicates = cursor.fetchall()
        
        print(f"Found {len(duplicates)} groups of duplicates")
        
        total_duplicates = 0
        duplicate_ids_to_remove = []
        
        for row in duplicates:
            species, date, source, raw_text, location, count, ids, dates = row
            total_duplicates += count - 1  # Keep one, remove the rest
            
            # Keep the first one (oldest), remove the rest
            ids_to_remove = ids[1:]  # Skip the first ID
            duplicate_ids_to_remove.extend(ids_to_remove)
            
            print(f"\nSpecies: {species}, Date: {date}, Source: {source}")
            print(f"Location: {location}")
            print(f"Text preview: {raw_text[:100] if raw_text else 'None'}...")
            print(f"Found {count} duplicates, will remove {count-1}")
            print(f"Keeping ID: {ids[0]} (created: {dates[0]})")
            print(f"Removing IDs: {ids_to_remove}")
        
        return duplicate_ids_to_remove, total_duplicates
        
    finally:
        cursor.close()
        conn.close()

def remove_duplicates(ids_to_remove):
    """Remove duplicate entries from the database."""
    if not ids_to_remove:
        print("No duplicates to remove")
        return
    
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    try:
        # Convert UUID strings to proper format for PostgreSQL
        print(f"\nRemoving {len(ids_to_remove)} duplicate entries...")
        
        # Delete in batches of 100
        batch_size = 100
        for i in range(0, len(ids_to_remove), batch_size):
            batch = ids_to_remove[i:i + batch_size]
            placeholders = ','.join(['%s'] * len(batch))
            
            delete_query = f"DELETE FROM sightings WHERE id IN ({placeholders})"
            cursor.execute(delete_query, batch)
            
            print(f"Deleted batch {i//batch_size + 1}: {cursor.rowcount} rows")
        
        conn.commit()
        print(f"\nSuccessfully removed {len(ids_to_remove)} duplicate entries")
        
    except Exception as e:
        conn.rollback()
        print(f"Error removing duplicates: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def update_content_hashes():
    """Update content_hash for remaining entries to prevent future duplicates."""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    try:
        # Update content hashes for entries that don't have them
        print("\nUpdating content hashes for entries without them...")
        
        cursor.execute("""
            SELECT id, species, sighting_date, source_type, raw_text, location_name
            FROM sightings
            WHERE content_hash IS NULL
        """)
        
        entries = cursor.fetchall()
        updated = 0
        
        for entry in entries:
            id_val, species, date, source, raw_text, location = entry
            
            # Generate content hash
            hash_val = generate_content_hash(
                species or '', 
                str(date) if date else '',
                source or '',
                raw_text or '',
                location or ''
            )
            
            cursor.execute(
                "UPDATE sightings SET content_hash = %s WHERE id = %s",
                (hash_val, id_val)
            )
            updated += 1
            
            if updated % 100 == 0:
                print(f"Updated {updated} entries...")
        
        conn.commit()
        print(f"Updated content hashes for {updated} entries")
        
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to clean up duplicates."""
    print("=== Wildlife Sightings Duplicate Cleanup ===\n")
    
    # Find duplicates
    ids_to_remove, total_count = find_duplicates()
    
    if total_count == 0:
        print("\nNo duplicates found!")
        return
    
    print(f"\nTotal duplicate entries to remove: {total_count}")
    
    # Confirm before removing
    response = input("\nDo you want to remove these duplicates? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return
    
    # Remove duplicates
    remove_duplicates(ids_to_remove)
    
    # Update content hashes
    response = input("\nDo you want to update content hashes to prevent future duplicates? (yes/no): ")
    if response.lower() == 'yes':
        update_content_hashes()
    
    print("\n=== Cleanup Complete ===")

if __name__ == "__main__":
    main()