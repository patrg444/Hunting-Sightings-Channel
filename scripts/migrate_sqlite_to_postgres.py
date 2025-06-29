#!/usr/bin/env python3
"""
Migrate data from SQLite (scrapers) to PostgreSQL (backend).
Maps field names and transforms data to match backend expectations.
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_data():
    """Migrate wildlife sightings from SQLite to PostgreSQL."""
    
    # SQLite connection
    sqlite_path = "backend/hunting_sightings.db"
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # PostgreSQL connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hunting_sightings')
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    
    pg_conn = psycopg2.connect(
        host=parsed.hostname or 'localhost',
        port=parsed.port or 5432,
        user=parsed.username or 'postgres',
        password=parsed.password or 'postgres',
        database=parsed.path.lstrip('/') or 'hunting_sightings'
    )
    pg_cursor = pg_conn.cursor()
    
    try:
        # Get all sightings from SQLite
        sqlite_cursor.execute("SELECT * FROM wildlife_sightings ORDER BY created_at")
        sightings = sqlite_cursor.fetchall()
        
        logger.info(f"Found {len(sightings)} sightings to migrate")
        
        migrated = 0
        skipped = 0
        
        for sighting in sightings:
            try:
                # Map fields from SQLite to PostgreSQL schema
                # Convert location to PostGIS point if we have coordinates
                location = None
                if sighting['latitude'] and sighting['longitude']:
                    location = f"POINT({sighting['longitude']} {sighting['latitude']})"
                
                # Map date field to sighting_date
                sighting_date = sighting['date']
                if isinstance(sighting_date, str):
                    try:
                        sighting_date = datetime.fromisoformat(sighting_date.replace('Z', '+00:00'))
                    except:
                        sighting_date = None
                
                # Insert into PostgreSQL with field mapping
                pg_cursor.execute("""
                    INSERT INTO sightings (
                        species,
                        raw_text,
                        keyword_matched,
                        source_url,
                        source_type,
                        extracted_at,
                        trail_name,
                        sighting_date,
                        gmu_unit,
                        location,
                        confidence_score,
                        created_at,
                        content_hash,
                        location_confidence_radius
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        ST_GeogFromText(%s), %s, %s, %s, %s
                    )
                    ON CONFLICT (content_hash) DO NOTHING
                """, (
                    sighting['species'],
                    sighting['description'] or '',  # map description to raw_text
                    None,  # keyword_matched not in SQLite
                    sighting['source_url'] or '',
                    sighting['source_type'] or 'unknown',
                    datetime.now(),  # extracted_at - use current time
                    sighting['location_name'],  # map location_name to trail_name
                    sighting_date,
                    sighting['gmu'],
                    location,
                    sighting['confidence_score'] or 0.8,
                    sighting['created_at'] or datetime.now(),
                    sighting['content_hash'],
                    None  # location_confidence_radius will come from fresh scrape
                ))
                
                migrated += 1
                
            except psycopg2.IntegrityError:
                # Duplicate content_hash
                skipped += 1
            except Exception as e:
                logger.error(f"Error migrating sighting {sighting['id']}: {e}")
                logger.debug(f"Sighting data: {dict(sighting)}")
        
        pg_conn.commit()
        logger.success(f"Migration complete! Migrated: {migrated}, Skipped (duplicates): {skipped}")
        
        # Verify migration
        pg_cursor.execute("SELECT COUNT(*) FROM sightings")
        count = pg_cursor.fetchone()[0]
        logger.info(f"Total sightings in PostgreSQL: {count}")
        
        # Show sample data
        pg_cursor.execute("""
            SELECT species, source_type, COUNT(*) as count 
            FROM sightings 
            GROUP BY species, source_type 
            ORDER BY count DESC 
            LIMIT 10
        """)
        results = pg_cursor.fetchall()
        logger.info("Top species/source combinations:")
        for species, source, count in results:
            logger.info(f"  {species} from {source}: {count}")
        
    except Exception as e:
        pg_conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    # First ensure the PostgreSQL schema exists
    logger.info("Creating PostgreSQL schema...")
    os.system("python scripts/create_backend_database_schema.py")
    
    # Then migrate the data
    logger.info("\nMigrating data from SQLite to PostgreSQL...")
    migrate_data()