"""
Database saving utilities for scrapers to save incrementally.
"""

import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any
import psycopg2
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

def save_sightings_to_db(sightings: List[Dict[str, Any]], source_name: str) -> int:
    """
    Save sightings to the database with deduplication.
    
    Args:
        sightings: List of sighting dictionaries
        source_name: Name of the source (e.g., 'reddit_cohunting')
        
    Returns:
        Number of sightings saved
    """
    
    # Get database connection
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        # Try Supabase
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
        
        if SUPABASE_URL and SUPABASE_KEY:
            # Use Supabase
            try:
                from supabase import create_client
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                saved_count = 0
                for sighting in sightings:
                    # Convert all datetime objects to ISO strings
                    for key, value in list(sighting.items()):
                        if hasattr(value, 'isoformat'):
                            sighting[key] = value.isoformat()
                    
                    # Add metadata
                    sighting['created_at'] = datetime.now().isoformat()
                    sighting['updated_at'] = datetime.now().isoformat()
                    
                    # Generate content hash for deduplication
                    content = f"{sighting.get('species', '')}_{sighting.get('location_name', '')}_{sighting.get('sighting_date', '')}"
                    sighting['content_hash'] = hashlib.md5(content.encode()).hexdigest()
                    
                    try:
                        # Map fields to match Supabase schema
                        supabase_sighting = {
                            'species': sighting.get('species'),
                            'sighting_date': sighting.get('sighting_date'),
                            'location_name': sighting.get('location_name'),
                            'location_confidence_radius': sighting.get('location_confidence_radius'),
                            'gmu_unit': sighting.get('gmu_number'),
                            'source_type': sighting.get('source_type'),
                            'source_url': sighting.get('source_url'),
                            'description': sighting.get('location_description'),
                            'confidence_score': sighting.get('confidence'),
                            'raw_text': sighting.get('raw_text'),
                            'content_hash': sighting.get('content_hash'),
                            'created_at': sighting.get('created_at'),
                            'updated_at': sighting.get('updated_at')
                        }
                        
                        # Add coordinates if available
                        if sighting.get('coordinates'):
                            coords = sighting['coordinates']
                            if isinstance(coords, list) and len(coords) == 2:
                                lat, lng = coords[0], coords[1]
                                # PostGIS format for Supabase
                                supabase_sighting['location'] = f'POINT({lng} {lat})'
                        
                        # Insert to Supabase
                        response = supabase.table('sightings').insert(supabase_sighting).execute()
                        if response.data:
                            saved_count += 1
                            logger.debug(f"Successfully saved: {sighting.get('species')} at {sighting.get('location_name')}")
                        else:
                            logger.warning(f"No data in response: {response}")
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            logger.debug(f"Duplicate sighting skipped: {sighting.get('species')} at {sighting.get('location_name')}")
                        else:
                            logger.warning(f"Failed to save sighting: {e}")
                            logger.debug(f"Sighting data that failed: {sighting}")
                
                logger.success(f"Saved {saved_count} sightings from {source_name} to Supabase")
                return saved_count
                
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                return 0
    
    # PostgreSQL connection
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        saved_count = 0
        duplicate_count = 0
        
        for sighting in sightings:
            # Generate content hash for deduplication
            content = f"{sighting.get('species', '')}_{sighting.get('location_name', '')}_{sighting.get('sighting_date', '')}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            try:
                cursor.execute("""
                    INSERT INTO wildlife_sightings (
                        species, confidence, location_name, location_confidence_radius,
                        sighting_date, source_type, source_url, raw_text,
                        gmu_number, county, coordinates, elevation, location_description,
                        content_hash, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (content_hash) DO NOTHING
                """, (
                    sighting.get('species'),
                    sighting.get('confidence'),
                    sighting.get('location_name'),
                    sighting.get('location_confidence_radius'),
                    sighting.get('sighting_date'),
                    sighting.get('source_type', source_name),
                    sighting.get('source_url'),
                    sighting.get('raw_text'),
                    sighting.get('gmu_number'),
                    sighting.get('county'),
                    sighting.get('coordinates'),
                    sighting.get('elevation'),
                    sighting.get('location_description'),
                    content_hash
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    duplicate_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to save sighting: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"{source_name}: Saved {saved_count} new sightings ({duplicate_count} duplicates skipped)")
        return saved_count
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return 0