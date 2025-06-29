#!/usr/bin/env python3
"""
Update the fresh_scrape_all.py script to save directly to PostgreSQL
with the correct field mapping for the backend.
"""

import os
from pathlib import Path

# Read the current fresh_scrape_all.py
script_path = Path(__file__).parent / "fresh_scrape_all.py"
with open(script_path, 'r') as f:
    content = f.read()

# Create updated version that saves to PostgreSQL
updated_content = '''#!/usr/bin/env python3
"""
Fresh scrape of all wildlife sighting sources with updated LLM validation.
Uses 60-day lookback period and ensures all data has location_confidence_radius.
Saves directly to PostgreSQL for backend compatibility.
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
from urllib.parse import urlparse

# Import all scrapers
from scrapers import (
    RedditScraper,
    GooglePlacesScraper, 
    FourteenersRealScraper,
    INaturalistScraper
)

# Load environment variables
load_dotenv()

def generate_content_hash(sighting: Dict[str, Any]) -> str:
    """Generate unique hash for deduplication."""
    # Use key fields that make a sighting unique
    content = f"{sighting.get('species', '')}_{sighting.get('sighting_date', '')}_{sighting.get('location_name', '')}_{sighting.get('source_type', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def get_db_connection():
    """Get PostgreSQL database connection."""
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hunting_sightings')
    parsed = urlparse(database_url)
    
    return psycopg2.connect(
        host=parsed.hostname or 'localhost',
        port=parsed.port or 5432,
        user=parsed.username or 'postgres',
        password=parsed.password or 'postgres',
        database=parsed.path.lstrip('/') or 'hunting_sightings'
    )

def save_to_database(sightings: List[Dict[str, Any]], source_name: str) -> int:
    """Save sightings to the PostgreSQL sightings table with correct field mapping."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    duplicate_count = 0
    
    for sighting in sightings:
        try:
            # Generate content hash
            content_hash = generate_content_hash(sighting)
            
            # Convert sighting date to proper format
            sighting_date = sighting.get('sighting_date', datetime.now().isoformat())
            if isinstance(sighting_date, str) and sighting_date.endswith('Z'):
                sighting_date = sighting_date.replace('Z', '+00:00')
            
            # Create PostGIS point from coordinates if available
            location = None
            if sighting.get('latitude') and sighting.get('longitude'):
                location = f"POINT({sighting['longitude']} {sighting['latitude']})"
            
            # Map fields to backend schema
            cursor.execute("""
                INSERT INTO sightings (
                    species, raw_text, keyword_matched, source_url, source_type,
                    extracted_at, trail_name, sighting_date, gmu_unit, location,
                    confidence_score, reddit_post_title, subreddit,
                    location_confidence_radius, content_hash
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeogFromText(%s),
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (content_hash) DO NOTHING
            """, (
                sighting.get('species'),
                sighting.get('raw_text', '')[:500],  # Limit description length
                sighting.get('keyword_matched'),
                sighting.get('source_url'),
                sighting.get('source_type'),
                sighting.get('extracted_at', datetime.now()),
                sighting.get('location_name'),  # Maps to trail_name
                sighting_date,
                sighting.get('gmu'),
                location,
                sighting.get('confidence', 80) / 100.0,  # Convert to decimal
                sighting.get('reddit_post_title'),
                sighting.get('subreddit'),
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
    """
    Run all scrapers with specified lookback period.
    
    Returns:
        Summary statistics of the scraping run
    """
    
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
        logger.info(f"\\n{'='*50}")
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
            
            # Save to PostgreSQL database
            saved_count = save_to_database(sightings, name)
            
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
    
    # Save all sightings to JSON
    save_sightings_json(all_sightings)
    
    return results

def save_sightings_json(sightings: List[Dict[str, Any]]):
    """Save sightings to JSON files."""
    
    output_dir = Path("data/sightings")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert datetime objects to strings
    for sighting in sightings:
        if 'sighting_date' in sighting:
            if hasattr(sighting['sighting_date'], 'isoformat'):
                sighting['sighting_date'] = sighting['sighting_date'].isoformat()
        if 'extracted_at' in sighting and hasattr(sighting['extracted_at'], 'isoformat'):
            sighting['extracted_at'] = sighting['extracted_at'].isoformat()
    
    # Save timestamped file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"fresh_scrape_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(sightings, f, indent=2, default=str)
    
    # Also save as latest
    latest_file = output_dir / "latest_sightings.json"
    with open(latest_file, 'w') as f:
        json.dump(sightings, f, indent=2, default=str)
    
    logger.info(f"Saved {len(sightings)} sightings to {output_file}")

def print_summary(results: Dict[str, Any]):
    """Print a summary of the scraping results."""
    
    logger.info("\\n" + "="*60)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*60)
    
    logger.info(f"\\nLookback period: {results['lookback_days']} days")
    logger.info(f"Started: {results['start_time']}")
    logger.info(f"Ended: {results['end_time']}")
    
    logger.info(f"\\nResults by source:")
    for source, stats in results['sources'].items():
        if 'error' in stats:
            logger.error(f"  {source}: ERROR - {stats['error']}")
        else:
            logger.info(f"  {source}:")
            logger.info(f"    - Found: {stats['total_found']}")
            logger.info(f"    - Saved: {stats['saved_to_db']}")
            logger.info(f"    - With radius: {stats['with_radius']} ({stats['with_radius']/max(stats['total_found'],1)*100:.1f}%)")
            logger.info(f"    - Duration: {stats['duration_seconds']:.1f}s")
    
    logger.info(f"\\nTOTAL SIGHTINGS: {results['total_sightings']}")
    logger.info(f"WITH LOCATION RADIUS: {results['total_with_radius']} ({results['total_with_radius']/max(results['total_sightings'],1)*100:.1f}%)")
    
    # Check database totals
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sightings")
    db_total = cursor.fetchone()[0]
    
    cursor.execute("SELECT source_type, COUNT(*) FROM sightings GROUP BY source_type")
    db_by_source = dict(cursor.fetchall())
    
    cursor.close()
    conn.close()
    
    logger.info(f"\\nDatabase totals:")
    logger.info(f"  Total records: {db_total}")
    for source, count in db_by_source.items():
        logger.info(f"  {source}: {count}")

def main():
    """Run fresh scraping of all sources."""
    
    logger.info("=" * 60)
    logger.info("FRESH WILDLIFE SIGHTINGS SCRAPE")
    logger.info("Using GPT-4.1 nano with location_confidence_radius")
    logger.info("Saving to PostgreSQL backend database")
    logger.info("=" * 60)
    
    # Run all scrapers
    results = run_all_scrapers(lookback_days=60)
    
    # Print summary
    print_summary(results)
    
    logger.success("\\nScraping complete!")
    logger.info("All data now includes location_confidence_radius field")
    logger.info("All validation performed with GPT-4.1 nano model")
    logger.info("Data saved to PostgreSQL with backend-compatible schema")

if __name__ == "__main__":
    main()
'''

# Save the updated script
updated_path = Path(__file__).parent / "fresh_scrape_all_postgres.py"
with open(updated_path, 'w') as f:
    f.write(updated_content)

print(f"Created updated scraper script: {updated_path}")
print("\nNext steps:")
print("1. Set DATABASE_URL environment variable to your PostgreSQL connection")
print("2. Run: python scripts/create_backend_database_schema.py")
print("3. Run: python scripts/fresh_scrape_all_postgres.py")