#!/usr/bin/env python3
"""
Fresh scrape of all wildlife sighting sources that saves directly to Supabase.
Uses 60-day lookback period and ensures all data has location_confidence_radius.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import psycopg2
from pathlib import Path
from loguru import logger
import hashlib
from dotenv import load_dotenv

# Import all scrapers
from scrapers import (
    RedditScraper,
    GooglePlacesScraper, 
    FourteenersRealScraper,
    INaturalistScraper
)

# Load environment variables
load_dotenv()

# Supabase database URL
SUPABASE_DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

def generate_content_hash(sighting: Dict[str, Any]) -> str:
    """Generate unique hash for deduplication."""
    content = f"{sighting.get('species', '')}_{sighting.get('sighting_date', '')}_{sighting.get('location_name', '')}_{sighting.get('source_type', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def save_to_supabase(sightings: List[Dict[str, Any]], source_name: str) -> int:
    """Save sightings to Supabase with correct field mapping."""
    
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()
    
    saved_count = 0
    duplicate_count = 0
    
    for sighting in sightings:
        try:
            # Generate content hash
            content_hash = generate_content_hash(sighting)
            
            # Convert sighting date to proper format
            sighting_date = sighting.get('sighting_date')
            if isinstance(sighting_date, str):
                try:
                    sighting_date = datetime.fromisoformat(sighting_date.replace('Z', '+00:00'))
                    sighting_date = sighting_date.date()  # Extract just the date
                except:
                    sighting_date = None
            elif hasattr(sighting_date, 'date'):
                sighting_date = sighting_date.date()
            
            # Create PostGIS point from coordinates if available
            location = None
            if sighting.get('latitude') and sighting.get('longitude'):
                location = f"POINT({sighting['longitude']} {sighting['latitude']})"
            
            # Map fields to Supabase schema
            cursor.execute("""
                INSERT INTO sightings (
                    species, raw_text, source_url, source_type,
                    extracted_at, location_name, sighting_date, gmu_unit, location,
                    confidence_score, location_confidence_radius, content_hash
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, ST_GeogFromText(%s),
                    %s, %s, %s
                )
                ON CONFLICT (content_hash) DO NOTHING
            """, (
                sighting.get('species'),
                sighting.get('raw_text', '')[:500],
                sighting.get('source_url'),
                sighting.get('source_type'),
                sighting.get('extracted_at', datetime.now()),
                sighting.get('location_name'),
                sighting_date,
                sighting.get('gmu'),
                location,
                sighting.get('confidence', 80) / 100.0,
                sighting.get('location_confidence_radius'),
                content_hash
            ))
            
            # Check if row was inserted
            if cursor.rowcount > 0:
                saved_count += 1
            else:
                duplicate_count += 1
                
        except Exception as e:
            logger.error(f"Error saving sighting: {e}")
            logger.debug(f"Sighting data: {sighting}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"{source_name}: Saved {saved_count} new sightings ({duplicate_count} duplicates skipped)")
    return saved_count

def run_all_scrapers(lookback_days: int = 60) -> Dict[str, Any]:
    """Run all scrapers with specified lookback period."""
    
    results = {
        'start_time': datetime.now().isoformat(),
        'lookback_days': lookback_days,
        'sources': {},
        'total_sightings': 0,
        'total_with_radius': 0
    }
    
    # Define scrapers to run
    scrapers = [
        ('Reddit', RedditScraper),
        ('Google Places', GooglePlacesScraper),
        ('14ers.com', FourteenersRealScraper),
        ('iNaturalist', INaturalistScraper)
    ]
    
    all_sightings = []
    
    for name, scraper_class in scrapers:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {name} scraper...")
        logger.info(f"{'='*50}")
        
        try:
            # Initialize scraper
            scraper = scraper_class()
            
            # Run scraping
            start_time = datetime.now()
            sightings = scraper.scrape(lookback_days=lookback_days)
            end_time = datetime.now()
            
            # Count sightings with location_confidence_radius
            with_radius = sum(1 for s in sightings if s.get('location_confidence_radius') is not None)
            
            # Save to Supabase
            saved_count = save_to_supabase(sightings, name)
            
            # Record results
            results['sources'][name] = {
                'total_found': len(sightings),
                'saved_to_db': saved_count,
                'with_radius': with_radius,
                'duration_seconds': (end_time - start_time).total_seconds()
            }
            
            # Add to combined list
            all_sightings.extend(sightings)
            
            logger.success(f"{name} complete: {len(sightings)} found, {with_radius} with radius")
            
        except Exception as e:
            logger.error(f"Error running {name} scraper: {e}")
            import traceback
            traceback.print_exc()
            results['sources'][name] = {'error': str(e)}
    
    # Calculate totals
    results['total_sightings'] = len(all_sightings)
    results['total_with_radius'] = sum(1 for s in all_sightings if s.get('location_confidence_radius') is not None)
    results['end_time'] = datetime.now().isoformat()
    
    return results

def print_summary(results: Dict[str, Any]):
    """Print a summary of the scraping results."""
    
    logger.info("\n" + "="*60)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*60)
    
    logger.info(f"\nLookback period: {results['lookback_days']} days")
    logger.info(f"Started: {results['start_time']}")
    logger.info(f"Ended: {results['end_time']}")
    
    logger.info(f"\nResults by source:")
    for source, stats in results['sources'].items():
        if 'error' in stats:
            logger.error(f"  {source}: ERROR - {stats['error']}")
        else:
            logger.info(f"  {source}:")
            logger.info(f"    - Found: {stats['total_found']}")
            logger.info(f"    - Saved: {stats['saved_to_db']}")
            logger.info(f"    - With radius: {stats['with_radius']} ({stats['with_radius']/max(stats['total_found'],1)*100:.1f}%)")
            logger.info(f"    - Duration: {stats['duration_seconds']:.1f}s")
    
    logger.info(f"\nTOTAL SIGHTINGS: {results['total_sightings']}")
    logger.info(f"WITH LOCATION RADIUS: {results['total_with_radius']} ({results['total_with_radius']/max(results['total_sightings'],1)*100:.1f}%)")
    
    # Check database totals
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sightings")
    db_total = cursor.fetchone()[0]
    
    cursor.execute("SELECT source_type, COUNT(*) FROM sightings GROUP BY source_type")
    db_by_source = dict(cursor.fetchall())
    
    cursor.close()
    conn.close()
    
    logger.info(f"\nSupabase database totals:")
    logger.info(f"  Total records: {db_total}")
    for source, count in db_by_source.items():
        logger.info(f"  {source}: {count}")

def main():
    """Run fresh scraping of all sources."""
    
    logger.info("=" * 60)
    logger.info("FRESH WILDLIFE SIGHTINGS SCRAPE TO SUPABASE")
    logger.info("Using GPT-4.1 nano with location_confidence_radius")
    logger.info("Saving directly to Supabase PostgreSQL")
    logger.info("=" * 60)
    
    # Test database connection
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        conn.close()
        logger.success("Successfully connected to Supabase database")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return
    
    # Run all scrapers
    results = run_all_scrapers(lookback_days=60)
    
    # Print summary
    print_summary(results)
    
    logger.success("\nScraping complete!")
    logger.info("All data saved to Supabase with location_confidence_radius field")

if __name__ == "__main__":
    main()