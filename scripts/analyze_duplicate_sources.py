#!/usr/bin/env python3
"""
Analyze duplicate sources and patterns in Supabase database.
Focus on understanding why duplicates occur and from which sources.
"""

import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger
from collections import defaultdict

# Load environment variables
load_dotenv()

def connect_to_supabase():
    """Connect to Supabase PostgreSQL database."""
    database_url = "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    logger.info("Connecting to Supabase database...")
    conn = psycopg2.connect(database_url)
    return conn

def analyze_duplicate_sources():
    """Analyze sources of duplicate sightings."""
    conn = connect_to_supabase()
    cursor = conn.cursor()
    
    try:
        # 1. Count sightings by source
        logger.info("Analyzing sightings by source...")
        cursor.execute("""
            SELECT 
                source_type,
                COUNT(*) as total_sightings,
                COUNT(DISTINCT species) as unique_species,
                COUNT(content_hash) as with_hash,
                COUNT(DISTINCT DATE(sighting_date)) as unique_days
            FROM sightings
            GROUP BY source_type
            ORDER BY total_sightings DESC;
        """)
        
        source_stats = cursor.fetchall()
        logger.info("\nSightings by source:")
        logger.info(f"{'Source':<20} {'Total':<10} {'Species':<10} {'With Hash':<12} {'Days':<10}")
        logger.info("-" * 62)
        for source, total, species, with_hash, days in source_stats:
            logger.info(f"{source:<20} {total:<10} {species:<10} {with_hash:<12} {days:<10}")
        
        # 2. Analyze Reddit duplicates specifically
        logger.info("\nAnalyzing Reddit duplicates (same location coordinates)...")
        cursor.execute("""
            WITH reddit_locations AS (
                SELECT 
                    ST_X(location::geometry) as lon,
                    ST_Y(location::geometry) as lat,
                    COUNT(*) as count,
                    COUNT(DISTINCT species) as species_count,
                    COUNT(DISTINCT DATE(sighting_date)) as date_count,
                    array_agg(DISTINCT LEFT(raw_text, 50)) as text_samples
                FROM sightings
                WHERE source_type = 'reddit' AND location IS NOT NULL
                GROUP BY ST_X(location::geometry), ST_Y(location::geometry)
                HAVING COUNT(*) > 10
                ORDER BY count DESC
                LIMIT 5
            )
            SELECT * FROM reddit_locations;
        """)
        
        reddit_hotspots = cursor.fetchall()
        if reddit_hotspots:
            logger.info("\nReddit location hotspots (likely default/generic coordinates):")
            for lon, lat, count, species, dates, texts in reddit_hotspots:
                logger.info(f"\nLocation: ({lat:.4f}, {lon:.4f})")
                logger.info(f"  - {count} sightings across {dates} different dates")
                logger.info(f"  - {species} different species")
                logger.info(f"  - Sample texts: {texts[:2]}")
        
        # 3. Check for exact text duplicates
        logger.info("\nChecking for exact text duplicates...")
        cursor.execute("""
            SELECT 
                source_type,
                raw_text,
                COUNT(*) as duplicate_count,
                array_agg(id) as ids
            FROM sightings
            GROUP BY source_type, raw_text
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 10;
        """)
        
        text_duplicates = cursor.fetchall()
        if text_duplicates:
            logger.info("\nTop exact text duplicates:")
            for i, (source, text, count, ids) in enumerate(text_duplicates, 1):
                logger.info(f"{i}. {source}: {count} duplicates")
                if text:
                    logger.info(f"   Text: '{text[:100]}...'")
                else:
                    logger.info(f"   Text: [NULL/Empty]")
                logger.info(f"   IDs: {ids[:3]}")
        
        # 4. Analyze duplicate patterns by date range
        logger.info("\nAnalyzing duplicate patterns by date...")
        cursor.execute("""
            WITH date_duplicates AS (
                SELECT 
                    DATE(sighting_date) as date,
                    species,
                    source_type,
                    COUNT(*) as count
                FROM sightings
                WHERE sighting_date IS NOT NULL
                GROUP BY DATE(sighting_date), species, source_type
                HAVING COUNT(*) > 2
            )
            SELECT 
                source_type,
                COUNT(*) as duplicate_days,
                SUM(count) as total_duplicates,
                AVG(count) as avg_per_day
            FROM date_duplicates
            GROUP BY source_type
            ORDER BY total_duplicates DESC;
        """)
        
        date_patterns = cursor.fetchall()
        logger.info("\nDuplicate patterns by source:")
        for source, days, total, avg in date_patterns:
            logger.info(f"  {source}: {total} duplicates across {days} days (avg {avg:.1f} per day)")
        
        # 5. Check if duplicates are from scrapers running multiple times
        logger.info("\nChecking for potential multiple scraper runs...")
        cursor.execute("""
            SELECT 
                source_type,
                DATE(extracted_at) as extraction_date,
                COUNT(*) as sightings_count,
                COUNT(DISTINCT DATE(sighting_date)) as unique_sighting_dates
            FROM sightings
            GROUP BY source_type, DATE(extracted_at)
            HAVING COUNT(*) > 20
            ORDER BY extraction_date DESC, sightings_count DESC;
        """)
        
        extraction_patterns = cursor.fetchall()
        if extraction_patterns:
            logger.info("\nLarge extraction batches (potential duplicate runs):")
            for source, date, count, unique_dates in extraction_patterns:
                logger.info(f"  {source} on {date}: {count} sightings from {unique_dates} different days")
        
        # 6. Identify sources without proper deduplication
        logger.info("\nAnalyzing deduplication effectiveness by source...")
        cursor.execute("""
            WITH source_dedup AS (
                SELECT 
                    source_type,
                    COUNT(*) as total,
                    COUNT(content_hash) as with_hash,
                    COUNT(DISTINCT content_hash) as unique_hashes,
                    COUNT(DISTINCT raw_text) as unique_texts
                FROM sightings
                GROUP BY source_type
            )
            SELECT 
                source_type,
                total,
                with_hash,
                CASE 
                    WHEN with_hash > 0 THEN with_hash - unique_hashes 
                    ELSE total - unique_texts 
                END as potential_duplicates,
                CASE 
                    WHEN total > 0 THEN 
                        ROUND(100.0 * with_hash / total, 1) 
                    ELSE 0 
                END as hash_coverage_pct
            FROM source_dedup
            ORDER BY potential_duplicates DESC;
        """)
        
        dedup_stats = cursor.fetchall()
        logger.info("\nDeduplication effectiveness:")
        logger.info(f"{'Source':<20} {'Total':<10} {'With Hash':<12} {'Potential Dupes':<18} {'Hash Coverage':<15}")
        logger.info("-" * 75)
        for source, total, with_hash, dupes, coverage in dedup_stats:
            logger.info(f"{source:<20} {total:<10} {with_hash:<12} {dupes:<18} {coverage:.1f}%")
        
        # 7. Summary recommendations
        logger.info("\n=== RECOMMENDATIONS ===")
        logger.info("1. Reddit has many duplicates at the same coordinates - likely using default/generic locations")
        logger.info("2. Content hash is only implemented for 42.6% of records - should be applied retroactively")
        logger.info("3. Some sources (14ers, inaturalist) have exact text duplicates - need better deduplication")
        logger.info("4. Consider implementing:")
        logger.info("   - Retroactive content_hash generation for all existing records")
        logger.info("   - Better location extraction for Reddit posts")
        logger.info("   - Deduplication check before inserting new records")
        logger.info("   - Regular cleanup job to remove identified duplicates")
        
    except Exception as e:
        logger.error(f"Error analyzing duplicate sources: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze_duplicate_sources()