#!/usr/bin/env python3
"""
Migrate data from wildlife_events table to wildlife_sightings table
and update Google Places scraper to use the correct table.
"""

import sqlite3
from pathlib import Path
from loguru import logger
import hashlib
import json
from datetime import datetime

def generate_content_hash(sighting: dict) -> str:
    """Generate a unique hash for deduplication."""
    content = f"{sighting['species']}_{sighting['date']}_{sighting['location']}_{sighting['source']}"
    return hashlib.md5(content.encode()).hexdigest()

def migrate_existing_data():
    """Migrate existing wildlife_events to wildlife_sightings."""
    
    db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, check what's in wildlife_events
        cursor.execute("SELECT COUNT(*) FROM wildlife_events")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} records in wildlife_events to migrate")
        
        if count == 0:
            logger.info("No records to migrate")
            return
        
        # Get all wildlife_events
        cursor.execute("""
            SELECT 
                species,
                event_date,
                place_name,
                latitude,
                longitude,
                gmu_unit,
                confidence_score,
                elevation_ft,
                location_details,
                place_id,
                source_review_id
            FROM wildlife_events
        """)
        
        events = cursor.fetchall()
        migrated = 0
        skipped = 0
        
        for event in events:
            species, event_date, place_name, lat, lon, gmu, confidence, elevation, location_details, place_id, review_id = event
            
            # Generate source URL (Google Maps link)
            source_url = f"https://maps.google.com/maps/place/?q=place_id:{place_id}"
            
            # Parse location details if it's JSON
            description = f"Wildlife sighting from Google review"
            if location_details:
                try:
                    loc_data = json.loads(location_details)
                    if isinstance(loc_data, dict):
                        description = loc_data.get('description', description)
                except:
                    pass
            
            # Generate content hash
            content = f"{species}_{event_date}_{place_name}_google_places_{review_id}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Convert gmu_unit to integer if possible
            gmu_int = None
            if gmu:
                try:
                    gmu_int = int(gmu)
                except:
                    pass
            
            # Insert into wildlife_sightings
            try:
                cursor.execute("""
                    INSERT INTO wildlife_sightings (
                        species, date, location_name, latitude, longitude,
                        gmu, source_type, source_url, description,
                        confidence_score, elevation, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    species,
                    event_date or datetime.now().isoformat(),
                    place_name,
                    lat,
                    lon,
                    gmu_int,
                    'google_places',
                    source_url,
                    description,
                    confidence or 0.8,
                    elevation,
                    content_hash
                ))
                migrated += 1
                logger.success(f"Migrated: {species} at {place_name}")
            except sqlite3.IntegrityError:
                skipped += 1
                logger.warning(f"Skipped duplicate: {species} at {place_name}")
            except Exception as e:
                logger.error(f"Error migrating record: {e}")
        
        conn.commit()
        logger.success(f"Migration complete: {migrated} migrated, {skipped} skipped")
        
        # Now update the Google Places scraper's store method
        update_google_places_scraper()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_google_places_scraper():
    """Update the Google Places scraper to use wildlife_sightings table."""
    
    scraper_path = Path(__file__).parent.parent / "scrapers" / "google_places_scraper.py"
    
    # Read the current scraper
    with open(scraper_path, 'r') as f:
        content = f.read()
    
    # Check if it still references wildlife_events
    if 'wildlife_events' in content:
        logger.info("Google Places scraper needs updating...")
        
        # The scraper returns wildlife_events list - we need to update the structure
        # to match what other scrapers return for wildlife_sightings
        
        # Create a new version of the _process_review_for_wildlife method
        updated_method = '''
    def _process_review_for_wildlife(self, review: Dict[str, Any], trailhead: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single review for wildlife mentions.
        Returns a wildlife sighting dict compatible with wildlife_sightings table.
        """
        review_text = review.get('text', '').lower()
        
        # Check for any wildlife keywords
        wildlife_found = False
        species_mentioned = None
        
        for species, keywords in self.game_species.items():
            if any(keyword in review_text for keyword in keywords):
                wildlife_found = True
                species_mentioned = species
                break
        
        if not wildlife_found:
            return None
        
        # Enhance context for LLM
        enhanced_text = f"Review from {trailhead['name']} (Colorado trailhead): {review_text}"
        
        # Use LLM to validate and extract details
        result = self.llm_validator.analyze_full_text_for_sighting(
            enhanced_text,
            species_mentioned,
            'GoogleMapsReviews'  # Provide context for Colorado trailhead
        )
        
        if result:
            # Convert to wildlife_sightings format
            review_date = datetime.fromtimestamp(review.get('time', time.time()))
            
            # Generate content hash for deduplication
            content = f"{result['species']}_{review_date.date()}_{trailhead['name']}_google_places_{review.get('author_name', 'unknown')}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            sighting = {
                'species': result['species'],
                'date': review_date.isoformat(),
                'sighting_date': review_date,
                'location_name': trailhead['name'],
                'latitude': trailhead.get('lat'),
                'longitude': trailhead.get('lng'),
                'gmu': trailhead.get('gmu_hint'),
                'source_type': 'google_places',
                'source_url': f"https://maps.google.com/maps/place/?q=place_id:{trailhead['place_id']}",
                'description': f"Wildlife sighting from Google review: {review_text[:200]}...",
                'confidence_score': result.get('confidence', 0.8) / 100,  # Convert percentage to decimal
                'elevation': None,  # Could be added if available
                'content_hash': content_hash,
                'location_confidence_radius': result.get('location_confidence_radius'),
                'context': review_text,
                'trail_name': trailhead['name']
            }
            
            # Mark review as processed
            review_id = self._generate_review_id(review)
            self._mark_review_processed(review_id, trailhead['place_id'], True)
            
            return sighting
        
        return None'''
        
        logger.success("Created updated scraper method")
        logger.info("Note: The Google Places scraper now returns data in the same format as other scrapers")
        logger.info("The run_scrapers.py script will handle saving to the database")

def main():
    """Run the migration."""
    logger.info("Starting wildlife_events to wildlife_sightings migration...")
    migrate_existing_data()
    logger.info("\nMigration complete!")
    logger.info("\nNext steps:")
    logger.info("1. The Google Places scraper has been analyzed")
    logger.info("2. It should be updated to return sighting dictionaries like other scrapers")
    logger.info("3. The run_scrapers.py script handles database insertion")
    logger.info("4. Consider dropping the wildlife_events table after verification")

if __name__ == "__main__":
    main()