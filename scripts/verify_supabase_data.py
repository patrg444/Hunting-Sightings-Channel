#!/usr/bin/env python3
"""
Verify recent sightings in Supabase database.
Check data integrity and search capabilities.
"""

import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger
from supabase import create_client

# Load environment variables
load_dotenv()

def verify_with_psycopg2():
    """Verify data using direct PostgreSQL connection."""
    logger.info("Verifying with PostgreSQL connection...")
    
    conn = psycopg2.connect(
        "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    )
    cursor = conn.cursor()
    
    # 1. Check total count
    cursor.execute("SELECT COUNT(*) FROM sightings")
    total = cursor.fetchone()[0]
    logger.info(f"Total sightings in database: {total}")
    
    # 2. Check recent entries (last 24 hours)
    cursor.execute("""
        SELECT 
            id,
            species,
            location_name,
            sighting_date,
            source_type,
            location_confidence_radius,
            created_at,
            ST_Y(location::geometry) as lat,
            ST_X(location::geometry) as lng
        FROM sightings
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    recent = cursor.fetchall()
    logger.info(f"\nFound {len(recent)} sightings created in last 24 hours:")
    
    for row in recent:
        id, species, location, date, source, radius, created, lat, lng = row
        coords = f"({lat:.4f}, {lng:.4f})" if lat and lng else "No coordinates"
        radius_str = f"{radius:.1f} mi" if radius else "No radius"
        logger.info(f"  {species} at {location or 'Unknown'} - {date} - {coords} - {radius_str} - from {source}")
    
    # 3. Check for today's Reddit sightings specifically
    cursor.execute("""
        SELECT 
            species,
            location_name,
            location_confidence_radius,
            description,
            raw_text
        FROM sightings
        WHERE source_type = 'reddit' 
        AND created_at >= NOW() - INTERVAL '2 hours'
        ORDER BY created_at DESC
    """)
    
    reddit_recent = cursor.fetchall()
    logger.info(f"\nRecent Reddit sightings (last 2 hours): {len(reddit_recent)}")
    
    for species, location, radius, desc, text in reddit_recent:
        logger.info(f"\n{species} sighting:")
        logger.info(f"  Location: {location or 'Unknown'}")
        logger.info(f"  Radius: {radius} miles" if radius else "  Radius: Not specified")
        logger.info(f"  Description: {desc or 'None'}")
        logger.info(f"  Text preview: {text[:100]}..." if text else "  No text")
    
    # 4. Check sightings with location confidence radius
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(location_confidence_radius) as min_radius,
            MAX(location_confidence_radius) as max_radius,
            AVG(location_confidence_radius) as avg_radius
        FROM sightings
        WHERE location_confidence_radius IS NOT NULL
    """)
    
    radius_stats = cursor.fetchone()
    total_with_radius, min_r, max_r, avg_r = radius_stats
    logger.info(f"\nLocation confidence radius statistics:")
    logger.info(f"  Total with radius: {total_with_radius}")
    logger.info(f"  Range: {min_r:.1f} - {max_r:.1f} miles")
    logger.info(f"  Average: {avg_r:.1f} miles")
    
    cursor.close()
    conn.close()

def verify_with_supabase_client():
    """Verify data using Supabase client."""
    logger.info("\nVerifying with Supabase client...")
    
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
    
    # 1. Recent sightings query
    response = supabase.table('sightings') \
        .select("*") \
        .gte('created_at', (datetime.now() - timedelta(hours=24)).isoformat()) \
        .order('created_at', desc=True) \
        .limit(5) \
        .execute()
    
    logger.info(f"\nSupabase client query - Recent 5 sightings:")
    for sighting in response.data:
        logger.info(f"  {sighting['species']} at {sighting.get('location_name', 'Unknown')} - {sighting['sighting_date']}")
    
    # 2. Search for bear sightings
    response = supabase.table('sightings') \
        .select("species, location_name, sighting_date, location_confidence_radius") \
        .eq('species', 'bear') \
        .order('sighting_date', desc=True) \
        .limit(5) \
        .execute()
    
    logger.info(f"\nRecent bear sightings: {len(response.data)}")
    for sighting in response.data:
        radius = sighting.get('location_confidence_radius')
        radius_str = f"{radius} mi" if radius else "No radius"
        logger.info(f"  {sighting['location_name'] or 'Unknown'} on {sighting['sighting_date']} - {radius_str}")
    
    # 3. Sightings with high confidence radius (specific locations)
    response = supabase.table('sightings') \
        .select("species, location_name, location_confidence_radius") \
        .lte('location_confidence_radius', 5) \
        .order('location_confidence_radius') \
        .limit(10) \
        .execute()
    
    logger.info(f"\nMost specific locations (radius <= 5 miles): {len(response.data)}")
    for sighting in response.data:
        logger.info(f"  {sighting['species']} at {sighting['location_name']} - {sighting['location_confidence_radius']} mi radius")

def search_specific_sightings():
    """Search for specific sightings we just added."""
    logger.info("\nSearching for sightings added in our test...")
    
    conn = psycopg2.connect(
        "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    )
    cursor = conn.cursor()
    
    # Look for the specific sightings we added
    test_queries = [
        ("Bear with 40 mile radius", """
            SELECT id, species, location_confidence_radius, created_at
            FROM sightings
            WHERE species = 'bear' 
            AND location_confidence_radius = 40
            AND created_at >= NOW() - INTERVAL '1 hour'
        """),
        
        ("Deer with 10 mile radius", """
            SELECT id, species, location_confidence_radius, created_at
            FROM sightings
            WHERE species = 'deer' 
            AND location_confidence_radius = 10
            AND created_at >= NOW() - INTERVAL '1 hour'
        """),
        
        ("All Reddit sightings today", """
            SELECT species, location_confidence_radius, created_at
            FROM sightings
            WHERE source_type = 'reddit'
            AND DATE(created_at) = CURRENT_DATE
            ORDER BY created_at DESC
        """)
    ]
    
    for name, query in test_queries:
        cursor.execute(query)
        results = cursor.fetchall()
        logger.info(f"\n{name}: {len(results)} found")
        for row in results:
            logger.info(f"  {row}")
    
    cursor.close()
    conn.close()

def main():
    """Run all verification checks."""
    logger.info("SUPABASE DATA VERIFICATION")
    logger.info("="*60)
    
    # Direct PostgreSQL verification
    verify_with_psycopg2()
    
    # Supabase client verification
    verify_with_supabase_client()
    
    # Search for specific test sightings
    search_specific_sightings()
    
    logger.info("\nVerification complete!")

if __name__ == "__main__":
    main()