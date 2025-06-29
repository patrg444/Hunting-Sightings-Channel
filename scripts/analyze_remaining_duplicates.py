#!/usr/bin/env python3
"""
Analyze remaining potential duplicates after aggressive deduplication.
These are sightings with same species, location, and date.
"""
import os
import sys
from datetime import datetime
import psycopg2
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def connect_to_supabase():
    """Connect to Supabase PostgreSQL database."""
    database_url = "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    logger.info("Connecting to Supabase database...")
    conn = psycopg2.connect(database_url)
    return conn

def analyze_remaining_duplicates():
    """Analyze remaining duplicates in detail."""
    conn = connect_to_supabase()
    cursor = conn.cursor()
    
    try:
        # Get detailed duplicate groups
        logger.info("Fetching remaining duplicate groups...")
        cursor.execute("""
            WITH duplicate_groups AS (
                SELECT 
                    species,
                    DATE(sighting_date) as sighting_day,
                    ST_X(location::geometry) as longitude,
                    ST_Y(location::geometry) as latitude,
                    COUNT(*) as duplicate_count,
                    array_agg(id) as ids,
                    array_agg(source_type) as sources,
                    array_agg(LEFT(raw_text, 100)) as text_previews,
                    array_agg(location_name) as location_names,
                    array_agg(content_hash) as hashes
                FROM sightings
                WHERE location IS NOT NULL 
                    AND sighting_date IS NOT NULL
                GROUP BY species, DATE(sighting_date), ST_X(location::geometry), ST_Y(location::geometry)
                HAVING COUNT(*) > 1
            )
            SELECT * FROM duplicate_groups
            ORDER BY duplicate_count DESC, sighting_day DESC
        """)
        
        duplicate_groups = cursor.fetchall()
        
        logger.info(f"\nFound {len(duplicate_groups)} groups of location-based duplicates")
        logger.info("="*80)
        
        # Categorize duplicates
        same_source_duplicates = []
        different_source_duplicates = []
        reddit_default_locations = []
        
        for group in duplicate_groups:
            species, date, lon, lat, count, ids, sources, texts, locations, hashes = group
            unique_sources = list(set(sources))
            
            # Check if it's a Reddit default location
            if abs(lon - (-105.7821)) < 0.001 and abs(lat - 39.5501) < 0.001:
                reddit_default_locations.append(group)
            elif abs(lon - (-105.5217)) < 0.001 and abs(lat - 40.3773) < 0.001:
                reddit_default_locations.append(group)
            elif len(unique_sources) == 1:
                same_source_duplicates.append(group)
            else:
                different_source_duplicates.append(group)
        
        # 1. Analyze same-source duplicates
        logger.info(f"\n1. SAME-SOURCE DUPLICATES ({len(same_source_duplicates)} groups)")
        logger.info("These might be actual duplicates that need resolution:")
        logger.info("-"*80)
        
        for i, group in enumerate(same_source_duplicates[:10], 1):
            species, date, lon, lat, count, ids, sources, texts, locations, hashes = group
            logger.info(f"\n{i}. {species} at ({lat:.4f}, {lon:.4f}) on {date}")
            logger.info(f"   Source: {sources[0]} ({count} records)")
            logger.info(f"   Location names: {list(set(filter(None, locations)))}")
            
            # Check if texts are different
            unique_texts = list(set(filter(None, texts)))
            if len(unique_texts) > 1:
                logger.info("   Different texts - likely different sightings:")
                for j, text in enumerate(unique_texts[:2], 1):
                    logger.info(f"     Text {j}: {text}...")
            else:
                logger.info("   Same/no text - might be true duplicates")
                logger.warning(f"   IDs to check: {ids}")
        
        # 2. Analyze Reddit default locations
        logger.info(f"\n2. REDDIT DEFAULT LOCATION DUPLICATES ({len(reddit_default_locations)} groups)")
        logger.info("These are likely different sightings with generic coordinates:")
        logger.info("-"*80)
        
        for group in reddit_default_locations[:5]:
            species, date, lon, lat, count, ids, sources, texts, locations, hashes = group
            logger.info(f"\n{species} on {date}: {count} sightings at default location ({lat:.4f}, {lon:.4f})")
            unique_locations = list(set(filter(None, locations)))
            if unique_locations:
                logger.info(f"   Actual locations mentioned: {unique_locations[:3]}")
        
        # 3. Analyze cross-source duplicates
        logger.info(f"\n3. CROSS-SOURCE DUPLICATES ({len(different_source_duplicates)} groups)")
        logger.info("These are from different sources - likely legitimate separate reports:")
        logger.info("-"*80)
        
        for group in different_source_duplicates[:5]:
            species, date, lon, lat, count, ids, sources, texts, locations, hashes = group
            unique_sources = list(set(sources))
            logger.info(f"\n{species} at ({lat:.4f}, {lon:.4f}) on {date}")
            logger.info(f"   Sources: {unique_sources} ({count} total)")
            logger.info(f"   Likely independent reports of same animal")
        
        # 4. Summary recommendations
        logger.info("\n" + "="*80)
        logger.info("SUMMARY AND RECOMMENDATIONS")
        logger.info("="*80)
        
        logger.info(f"\nTotal remaining duplicate groups: {len(duplicate_groups)}")
        logger.info(f"- Same-source duplicates: {len(same_source_duplicates)} (need review)")
        logger.info(f"- Reddit default locations: {len(reddit_default_locations)} (not true duplicates)")
        logger.info(f"- Cross-source duplicates: {len(different_source_duplicates)} (legitimate)")
        
        logger.info("\nRECOMMENDATIONS:")
        logger.info("1. Same-source duplicates with identical text should be merged")
        logger.info("2. Reddit default location 'duplicates' should be left as-is")
        logger.info("   (they're different sightings with imprecise coordinates)")
        logger.info("3. Cross-source duplicates should remain separate")
        logger.info("   (independent reports of the same wildlife)")
        
        # Export detailed analysis
        if same_source_duplicates:
            logger.info("\nExporting detailed analysis for manual review...")
            
            with open('remaining_duplicates_analysis.txt', 'w') as f:
                f.write("REMAINING DUPLICATES ANALYSIS\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("="*80 + "\n\n")
                
                f.write("SAME-SOURCE DUPLICATES REQUIRING REVIEW:\n")
                f.write("-"*80 + "\n")
                
                for group in same_source_duplicates:
                    species, date, lon, lat, count, ids, sources, texts, locations, hashes = group
                    f.write(f"\n{species} at ({lat:.4f}, {lon:.4f}) on {date}\n")
                    f.write(f"Source: {sources[0]} ({count} records)\n")
                    f.write(f"IDs: {ids}\n")
                    f.write(f"Hashes: {hashes}\n")
                    
                    unique_texts = list(set(filter(None, texts)))
                    if len(unique_texts) == 1:
                        f.write("Status: LIKELY DUPLICATE (same text)\n")
                    else:
                        f.write("Status: DIFFERENT SIGHTINGS (different texts)\n")
                    f.write("\n")
            
            logger.info("Analysis saved to: remaining_duplicates_analysis.txt")
        
    except Exception as e:
        logger.error(f"Error analyzing duplicates: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze_remaining_duplicates()