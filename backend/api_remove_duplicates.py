#!/usr/bin/env python3
"""
API endpoint to remove duplicate sightings.
This can be added to the main API or run as a standalone script.
"""

import psycopg2
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Dict, Optional
import hashlib
from datetime import datetime

app = FastAPI()

DB_URL = "postgresql://patrickgloria:wildlifetracker2024@localhost:5432/wildlife_sightings_db"

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(DB_URL)

def generate_content_hash(species, date, source, raw_text, location):
    """Generate a hash for deduplication."""
    content = f"{species}|{date}|{source}|{raw_text}|{location}"
    return hashlib.sha256(content.encode()).hexdigest()

@app.get("/api/v1/duplicates/check")
def check_duplicates(
    species: Optional[str] = None,
    source_type: Optional[str] = None,
    date: Optional[str] = None
):
    """Check for duplicate entries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build query
        query = """
            SELECT 
                species, sighting_date, source_type, raw_text, location_name,
                COUNT(*) as duplicate_count,
                ARRAY_AGG(id ORDER BY created_at ASC) as ids,
                MIN(created_at) as oldest_date,
                MAX(created_at) as newest_date
            FROM sightings
            WHERE content_hash IS NULL
        """
        
        params = []
        if species:
            query += " AND LOWER(species) = LOWER(%s)"
            params.append(species)
        if source_type:
            query += " AND LOWER(source_type) = LOWER(%s)"
            params.append(source_type)
        if date:
            query += " AND sighting_date::date = %s"
            params.append(date)
            
        query += """
            GROUP BY species, sighting_date, source_type, raw_text, location_name
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
        """
        
        cursor.execute(query, params)
        
        results = []
        total_duplicates = 0
        
        for row in cursor.fetchall():
            species, date, source, raw_text, location, count, ids, oldest, newest = row
            total_duplicates += count - 1
            
            results.append({
                "species": species,
                "date": str(date),
                "source": source,
                "location": location,
                "text_preview": raw_text[:100] if raw_text else None,
                "duplicate_count": count,
                "duplicate_ids": ids[1:],  # IDs to remove (keeping the first)
                "keeping_id": ids[0],
                "oldest_created": str(oldest),
                "newest_created": str(newest)
            })
        
        return {
            "total_groups": len(results),
            "total_duplicates_to_remove": total_duplicates,
            "duplicate_groups": results
        }
        
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/v1/duplicates/remove")
def remove_duplicates(
    ids: List[str] = Query(..., description="List of IDs to remove"),
    dry_run: bool = Query(False, description="If true, only simulate the deletion")
):
    """Remove specific duplicate entries."""
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if dry_run:
            # Just count how many would be deleted
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(
                f"SELECT COUNT(*) FROM sightings WHERE id IN ({placeholders})",
                ids
            )
            count = cursor.fetchone()[0]
            return {
                "dry_run": True,
                "would_delete": count,
                "ids": ids
            }
        else:
            # Actually delete
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(
                f"DELETE FROM sightings WHERE id IN ({placeholders}) RETURNING id",
                ids
            )
            deleted_ids = [row[0] for row in cursor.fetchall()]
            conn.commit()
            
            return {
                "deleted": len(deleted_ids),
                "ids": deleted_ids
            }
            
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/v1/duplicates/remove-all")
def remove_all_duplicates(
    species: Optional[str] = None,
    source_type: Optional[str] = None,
    date: Optional[str] = None,
    dry_run: bool = Query(True, description="If true, only simulate the deletion")
):
    """Remove all duplicates matching criteria, keeping the oldest entry."""
    # First, get all duplicates
    duplicates = check_duplicates(species, source_type, date)
    
    if duplicates["total_duplicates_to_remove"] == 0:
        return {"message": "No duplicates found", "deleted": 0}
    
    # Collect all IDs to remove
    all_ids_to_remove = []
    for group in duplicates["duplicate_groups"]:
        all_ids_to_remove.extend(group["duplicate_ids"])
    
    # Remove them
    result = remove_duplicates(ids=all_ids_to_remove, dry_run=dry_run)
    
    return {
        "groups_processed": duplicates["total_groups"],
        "total_duplicates": duplicates["total_duplicates_to_remove"],
        **result
    }

@app.patch("/api/v1/duplicates/update-hashes")
def update_content_hashes():
    """Update content hashes for entries that don't have them."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get entries without content hash
        cursor.execute("""
            SELECT id, species, sighting_date, source_type, raw_text, location_name
            FROM sightings
            WHERE content_hash IS NULL
            LIMIT 1000
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
        
        conn.commit()
        
        return {
            "updated": updated,
            "message": f"Updated content hashes for {updated} entries"
        }
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)