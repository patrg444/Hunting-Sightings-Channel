#!/usr/bin/env python3
"""
Analyze Supabase database for duplicate sightings.
Checks for duplicates by species, location, date, and analyzes content_hash usage.
"""

import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger
from datetime import datetime
import json

# Load environment variables
load_dotenv()

def connect_to_supabase():
    """Connect to Supabase PostgreSQL database."""
    database_url = "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    logger.info("Connecting to Supabase database...")
    conn = psycopg2.connect(database_url)
    return conn

def analyze_duplicates():
    """Analyze duplicate sightings in the database."""
    conn = connect_to_supabase()
    cursor = conn.cursor()
    
    try:
        # 1. Total number of sightings
        logger.info("Checking total number of sightings...")
        cursor.execute("SELECT COUNT(*) FROM sightings;")
        total_sightings = cursor.fetchone()[0]
        logger.info(f"Total sightings in database: {total_sightings}")
        
        # 2. Check content_hash usage
        logger.info("\nAnalyzing content_hash usage...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(content_hash) as with_hash,
                COUNT(DISTINCT content_hash) as unique_hashes
            FROM sightings;
        """)
        hash_stats = cursor.fetchone()
        logger.info(f"Total records: {hash_stats[0]}")
        logger.info(f"Records with content_hash: {hash_stats[1]}")
        logger.info(f"Unique content_hashes: {hash_stats[2]}")
        logger.info(f"Potential duplicates caught by content_hash: {hash_stats[1] - hash_stats[2] if hash_stats[2] else 0}")
        
        # 3. Find duplicates by species, location, and date
        logger.info("\nFinding duplicates by species, location, and date...")
        cursor.execute("""
            WITH duplicate_groups AS (
                SELECT 
                    species,
                    DATE(sighting_date) as sighting_day,
                    ST_X(location::geometry) as longitude,
                    ST_Y(location::geometry) as latitude,
                    COUNT(*) as duplicate_count,
                    array_agg(DISTINCT source_type) as sources,
                    array_agg(id) as sighting_ids
                FROM sightings
                WHERE location IS NOT NULL 
                    AND sighting_date IS NOT NULL
                GROUP BY species, DATE(sighting_date), ST_X(location::geometry), ST_Y(location::geometry)
                HAVING COUNT(*) > 1
            )
            SELECT * FROM duplicate_groups
            ORDER BY duplicate_count DESC
            LIMIT 20;
        """)
        
        exact_duplicates = cursor.fetchall()
        total_duplicate_groups = len(exact_duplicates)
        
        if exact_duplicates:
            logger.info(f"\nFound {total_duplicate_groups} groups of exact duplicates (same species, location, date)")
            logger.info("\nTop duplicate groups:")
            for i, (species, date, lon, lat, count, sources, ids) in enumerate(exact_duplicates[:10], 1):
                logger.info(f"{i}. {species} on {date} at ({lat:.4f}, {lon:.4f})")
                logger.info(f"   - {count} duplicates from sources: {sources}")
                logger.info(f"   - IDs: {ids[:3]}{'...' if len(ids) > 3 else ''}")
        
        # 4. Find near-duplicates (within 1km and same day)
        logger.info("\nFinding near-duplicates (within 1km, same day)...")
        cursor.execute("""
            WITH sighting_pairs AS (
                SELECT 
                    s1.id as id1,
                    s2.id as id2,
                    s1.species as species1,
                    s2.species as species2,
                    s1.source_type as source1,
                    s2.source_type as source2,
                    DATE(s1.sighting_date) as date1,
                    DATE(s2.sighting_date) as date2,
                    ST_Distance(s1.location, s2.location) as distance_meters
                FROM sightings s1
                JOIN sightings s2 ON s1.id < s2.id
                WHERE s1.location IS NOT NULL 
                    AND s2.location IS NOT NULL
                    AND s1.sighting_date IS NOT NULL
                    AND s2.sighting_date IS NOT NULL
                    AND s1.species = s2.species
                    AND DATE(s1.sighting_date) = DATE(s2.sighting_date)
                    AND ST_DWithin(s1.location, s2.location, 1000)  -- within 1km
            )
            SELECT 
                species1 as species,
                date1 as sighting_date,
                COUNT(*) as near_duplicate_pairs,
                AVG(distance_meters) as avg_distance,
                array_agg(DISTINCT source1) || array_agg(DISTINCT source2) as sources
            FROM sighting_pairs
            GROUP BY species1, date1
            ORDER BY near_duplicate_pairs DESC
            LIMIT 10;
        """)
        
        near_duplicates = cursor.fetchall()
        if near_duplicates:
            logger.info("\nTop near-duplicate groups (within 1km, same day):")
            for i, (species, date, pairs, avg_dist, sources) in enumerate(near_duplicates, 1):
                unique_sources = list(set(sources))
                logger.info(f"{i}. {species} on {date}")
                logger.info(f"   - {pairs} near-duplicate pairs")
                logger.info(f"   - Average distance: {avg_dist:.1f} meters")
                logger.info(f"   - Sources involved: {unique_sources}")
        
        # 5. Analyze duplicates by source
        logger.info("\nAnalyzing duplicate patterns by source...")
        cursor.execute("""
            WITH source_overlap AS (
                SELECT 
                    s1.source_type as source1,
                    s2.source_type as source2,
                    COUNT(*) as overlap_count
                FROM sightings s1
                JOIN sightings s2 ON s1.id != s2.id
                WHERE s1.location IS NOT NULL 
                    AND s2.location IS NOT NULL
                    AND s1.sighting_date IS NOT NULL
                    AND s2.sighting_date IS NOT NULL
                    AND s1.species = s2.species
                    AND DATE(s1.sighting_date) = DATE(s2.sighting_date)
                    AND ST_DWithin(s1.location, s2.location, 100)  -- within 100m
                    AND s1.source_type < s2.source_type  -- avoid counting pairs twice
                GROUP BY s1.source_type, s2.source_type
                ORDER BY overlap_count DESC
            )
            SELECT * FROM source_overlap;
        """)
        
        source_overlaps = cursor.fetchall()
        if source_overlaps:
            logger.info("\nSource overlap analysis (same species, location, date):")
            for source1, source2, count in source_overlaps:
                logger.info(f"  {source1} <-> {source2}: {count} potential duplicates")
        
        # 6. Check for duplicates without content_hash
        logger.info("\nChecking for duplicates among records without content_hash...")
        cursor.execute("""
            SELECT 
                species,
                source_type,
                COUNT(*) as count,
                COUNT(DISTINCT raw_text) as unique_texts
            FROM sightings
            WHERE content_hash IS NULL
            GROUP BY species, source_type
            HAVING COUNT(*) > COUNT(DISTINCT raw_text)
            ORDER BY (COUNT(*) - COUNT(DISTINCT raw_text)) DESC
            LIMIT 10;
        """)
        
        missing_hash_duplicates = cursor.fetchall()
        if missing_hash_duplicates:
            logger.info("\nPotential duplicates without content_hash:")
            for species, source, total, unique in missing_hash_duplicates:
                duplicates = total - unique
                logger.info(f"  {species} from {source}: {duplicates} potential duplicates ({total} total, {unique} unique texts)")
        
        # 7. Summary statistics
        logger.info("\n=== DUPLICATE ANALYSIS SUMMARY ===")
        logger.info(f"Total sightings: {total_sightings}")
        logger.info(f"Records with content_hash: {hash_stats[1]} ({hash_stats[1]/total_sightings*100:.1f}%)")
        logger.info(f"Exact duplicate groups found: {total_duplicate_groups}")
        
        # Calculate total duplicates
        cursor.execute("""
            SELECT SUM(count - 1) as total_exact_duplicates
            FROM (
                SELECT COUNT(*) as count
                FROM sightings
                WHERE location IS NOT NULL AND sighting_date IS NOT NULL
                GROUP BY species, DATE(sighting_date), ST_X(location::geometry), ST_Y(location::geometry)
                HAVING COUNT(*) > 1
            ) as dup_groups;
        """)
        total_exact_dupes = cursor.fetchone()[0] or 0
        logger.info(f"Total exact duplicate records: {total_exact_dupes} ({total_exact_dupes/total_sightings*100:.1f}%)")
        
        # Export detailed duplicate report
        logger.info("\nExporting detailed duplicate report...")
        cursor.execute("""
            WITH duplicate_details AS (
                SELECT 
                    s.*,
                    ST_X(s.location::geometry) as longitude,
                    ST_Y(s.location::geometry) as latitude
                FROM sightings s
                WHERE EXISTS (
                    SELECT 1 
                    FROM sightings s2 
                    WHERE s2.id != s.id
                        AND s2.species = s.species
                        AND DATE(s2.sighting_date) = DATE(s.sighting_date)
                        AND ST_DWithin(s2.location, s.location, 100)
                )
                ORDER BY s.species, s.sighting_date, s.source_type
            )
            SELECT 
                id,
                species,
                source_type,
                sighting_date,
                latitude,
                longitude,
                content_hash,
                LEFT(raw_text, 100) as raw_text_preview
            FROM duplicate_details
            LIMIT 100;
        """)
        
        duplicate_records = cursor.fetchall()
        
        with open('duplicate_analysis_report.json', 'w') as f:
            report = {
                'analysis_date': datetime.now().isoformat(),
                'summary': {
                    'total_sightings': total_sightings,
                    'records_with_content_hash': hash_stats[1],
                    'unique_content_hashes': hash_stats[2],
                    'exact_duplicate_groups': total_duplicate_groups,
                    'total_exact_duplicates': int(total_exact_dupes)
                },
                'sample_duplicates': [
                    {
                        'id': str(record[0]),
                        'species': record[1],
                        'source': record[2],
                        'date': record[3].isoformat() if record[3] else None,
                        'latitude': record[4],
                        'longitude': record[5],
                        'has_content_hash': bool(record[6]),
                        'text_preview': record[7]
                    }
                    for record in duplicate_records
                ]
            }
            json.dump(report, f, indent=2)
        
        logger.success("Analysis complete! Report saved to duplicate_analysis_report.json")
        
    except Exception as e:
        logger.error(f"Error analyzing duplicates: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze_duplicates()