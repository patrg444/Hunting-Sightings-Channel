#!/usr/bin/env python3
"""
Analyze the Google Places review cache to show wildlife sightings.
"""

import sqlite3
from pathlib import Path
from loguru import logger
import json

def analyze_cache():
    """Analyze the Google Places cache for wildlife mentions."""
    
    db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get summary stats
        cursor.execute("SELECT COUNT(*) FROM google_review_cache")
        total_reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM google_review_cache WHERE has_wildlife_mention = 1")
        wildlife_reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT place_id) FROM google_review_cache")
        total_places = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT place_id) FROM google_review_cache WHERE has_wildlife_mention = 1")
        places_with_wildlife = cursor.fetchone()[0]
        
        logger.info(f"Total reviews processed: {total_reviews}")
        logger.info(f"Reviews with wildlife mentions: {wildlife_reviews}")
        logger.info(f"Total places: {total_places}")
        logger.info(f"Places with wildlife sightings: {places_with_wildlife}")
        logger.info(f"Wildlife mention rate: {wildlife_reviews/total_reviews*100:.1f}%")
        
        # Get places with most wildlife mentions
        cursor.execute("""
            SELECT place_id, COUNT(*) as wildlife_count
            FROM google_review_cache
            WHERE has_wildlife_mention = 1
            GROUP BY place_id
            ORDER BY wildlife_count DESC
            LIMIT 10
        """)
        
        logger.info("\nTop places with wildlife mentions:")
        for place_id, count in cursor.fetchall():
            logger.info(f"  {place_id}: {count} mentions")
        
        # Load config to get place names
        config_path = Path(__file__).parent.parent / "data" / "google_places_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                place_names = {t['place_id']: t['name'] for t in config['trails']}
            
            logger.info("\nPlaces with wildlife sightings:")
            cursor.execute("""
                SELECT DISTINCT place_id 
                FROM google_review_cache 
                WHERE has_wildlife_mention = 1
            """)
            
            for (place_id,) in cursor.fetchall():
                name = place_names.get(place_id, "Unknown")
                logger.info(f"  - {name}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error analyzing cache: {e}")

if __name__ == "__main__":
    analyze_cache()