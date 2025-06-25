"""
Google Places API scraper for wildlife sightings in reviews.
Complies with Google's licensing by:
- Only fetching the latest 5 reviews per place
- Storing raw reviews for max 30 days
- Extracting and permanently storing only wildlife event data
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import hashlib

from .base import BaseScraper
from .llm_validator import LLMValidator


class GooglePlacesScraper(BaseScraper):
    """
    Scrapes Google Places reviews for wildlife sightings at Colorado trailheads.
    Complies with Google's Terms of Service by implementing proper data retention.
    """
    
    def __init__(self):
        super().__init__(source_name='google_places', rate_limit=0.5)  # 2 requests per second
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY not found in environment variables")
        
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.llm_validator = LLMValidator()
        
    def _get_colorado_trailhead_places(self) -> List[Dict[str, Any]]:
        """
        Get a list of popular Colorado trailhead place IDs.
        Loads from configuration file for easy management.
        """
        import json
        from pathlib import Path
        
        # Try to load from config file
        config_path = Path(__file__).parent.parent / "data" / "google_places_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                trails = config.get('trails', [])
                max_trails = config.get('max_trails_per_run', 30)
                
                # Return top trails up to max limit
                return trails[:max_trails]
                
            except Exception as e:
                logger.error(f"Failed to load Google Places config: {e}")
        
        # Fallback to a few hardcoded trails
        logger.warning("Using fallback trail list")
        return [
            {
                'place_id': 'ChIJ7d-_s1hAQIcR2uGf8E1ocJM',
                'name': 'Maroon Bells Scenic Area',
                'gmu_hint': 49
            },
            {
                'place_id': 'ChIJ0Zjur8F7aYcRWs6hl3IXMFg',
                'name': 'Emerald Lake',
                'gmu_hint': 20
            }
        ]
    
    def _fetch_place_reviews(self, place_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch the latest 5 reviews for a place using Google Places API.
        
        Args:
            place_id: Google Place ID
            
        Returns:
            List of review dictionaries or None if failed
        """
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'reviews',  # Only fetch reviews
            'key': self.api_key,
            'reviews_no_translations': 'true',  # Get original language only
            'reviews_sort': 'newest'  # Get most recent reviews
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return None
        
        try:
            data = response.json()
            if data.get('status') != 'OK':
                logger.error(f"Google Places API error: {data.get('status')}")
                return None
            
            reviews = data.get('result', {}).get('reviews', [])
            # Google returns up to 5 reviews by default
            return reviews[:5]  # Ensure we only use 5 reviews max
            
        except Exception as e:
            logger.error(f"Failed to parse Google Places response: {e}")
            return None
    
    def _generate_review_id(self, review_data: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a review based on its content.
        Google doesn't provide review IDs, so we create our own.
        """
        # Create hash from author, time, and first 100 chars of text
        content = f"{review_data.get('author_name', '')}"
        content += f"{review_data.get('time', '')}"
        content += f"{review_data.get('text', '')[:100]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _process_review_for_wildlife(self, review: Dict[str, Any], place_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single review to extract wildlife sighting information.
        
        Args:
            review: Google review data
            place_info: Information about the place (name, GMU hint, etc.)
            
        Returns:
            Wildlife event data if found, None otherwise
        """
        review_text = review.get('text', '')
        if not review_text:
            return None
        
        # Check if review mentions any wildlife species
        potential_mentions = self._extract_potential_wildlife_mentions(
            review_text, 
            f"https://maps.google.com/maps/place/?q=place_id:{place_info['place_id']}"
        )
        
        if not potential_mentions:
            return None
        
        # Use LLM to analyze the review for actual sightings
        for mention in potential_mentions:
            # Create a special prompt for Google review analysis
            review_date = datetime.fromtimestamp(review.get('time', 0))
            
            # Enhanced context for Google reviews
            enhanced_text = f"""
            Google Review for {place_info['name']} (Colorado trailhead)
            Review Date: {review_date.strftime('%Y-%m-%d')}
            Review: {review_text}
            """
            
            result = self.llm_validator.analyze_full_text_for_sighting(
                enhanced_text,
                mention['species_mentioned']
            )
            
            if result and result.get('is_sighting'):
                # Extract event date from review if mentioned, otherwise use review date
                event_date = result.get('event_date') or review_date.date()
                
                wildlife_event = {
                    'place_id': place_info['place_id'],
                    'species': result['species'],
                    'event_date': event_date,
                    'review_date': review_date.date(),
                    'source': 'google_review',
                    'confidence_score': result.get('confidence', 0.8),
                    'gmu_unit': result.get('gmu_number') or place_info.get('gmu_hint'),
                    'location_details': {
                        'place_name': place_info['name'],
                        'location_name': result.get('location_name'),
                        'elevation': result.get('elevation'),
                        'location_description': result.get('location_description')
                    }
                }
                
                return wildlife_event
        
        return None
    
    def _get_processed_review_ids(self) -> set:
        """Get set of already processed review IDs from cache."""
        processed_ids = set()
        
        try:
            import sqlite3
            from pathlib import Path
            db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all processed review IDs
            cursor.execute("SELECT review_id FROM google_review_cache")
            processed_ids = {row[0] for row in cursor.fetchall()}
            
            conn.close()
            logger.info(f"Loaded {len(processed_ids)} processed review IDs from cache")
            
        except Exception as e:
            logger.warning(f"Could not load review cache: {e}")
            
        return processed_ids
    
    def _mark_review_processed(self, review_id: str, place_id: str, has_wildlife: bool):
        """Mark a review as processed in the cache."""
        try:
            import sqlite3
            from pathlib import Path
            db_path = Path(__file__).parent.parent / "backend" / "hunting_sightings.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO google_review_cache 
                (review_id, place_id, has_wildlife_mention) 
                VALUES (?, ?, ?)
            """, (review_id, place_id, int(has_wildlife)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update review cache: {e}")
    
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape Google Places reviews for wildlife sightings.
        Only processes new reviews not in cache.
        
        Args:
            lookback_days: Not used for Google Places (we get latest reviews)
            
        Returns:
            List of wildlife sighting dictionaries
        """
        wildlife_events = []
        trailheads = self._get_colorado_trailhead_places()
        
        # Get already processed review IDs
        processed_ids = self._get_processed_review_ids()
        
        logger.info(f"Processing {len(trailheads)} Colorado trailheads for Google reviews")
        logger.info(f"Skipping {len(processed_ids)} already processed reviews")
        
        total_reviews = 0
        new_reviews = 0
        
        for trailhead in trailheads:
            logger.debug(f"Fetching reviews for {trailhead['name']}")
            
            reviews = self._fetch_place_reviews(trailhead['place_id'])
            if not reviews:
                continue
            
            total_reviews += len(reviews)
            
            for review in reviews:
                # Generate review ID for deduplication
                review_id = self._generate_review_id(review)
                
                # Skip if already processed
                if review_id in processed_ids:
                    logger.debug(f"Skipping already processed review {review_id}")
                    continue
                
                new_reviews += 1
                
                # Process review for wildlife mentions
                wildlife_event = self._process_review_for_wildlife(review, trailhead)
                
                # Mark as processed (whether wildlife found or not)
                self._mark_review_processed(
                    review_id, 
                    trailhead['place_id'], 
                    wildlife_event is not None
                )
                
                if wildlife_event:
                    # Add metadata for storage
                    wildlife_event['review_id'] = review_id
                    wildlife_event['raw_review_data'] = review  # For temporary storage
                    wildlife_events.append(wildlife_event)
                    
                    logger.info(f"Found {wildlife_event['species']} sighting in Google review at {trailhead['name']}")
        
        logger.info(f"Processed {new_reviews} new reviews out of {total_reviews} total")
        logger.info(f"Found {len(wildlife_events)} wildlife events in Google reviews")
        return wildlife_events
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Get trail location data from Google Places.
        
        Returns:
            List of trail dictionaries with name, lat, lon
        """
        locations = []
        trailheads = self._get_colorado_trailhead_places()
        
        for trailhead in trailheads:
            # Fetch place details including coordinates
            url = f"{self.base_url}/details/json"
            params = {
                'place_id': trailhead['place_id'],
                'fields': 'name,geometry',
                'key': self.api_key
            }
            
            response = self._make_request(url, params=params)
            if response:
                try:
                    data = response.json()
                    if data.get('status') == 'OK':
                        result = data.get('result', {})
                        geometry = result.get('geometry', {}).get('location', {})
                        
                        locations.append({
                            'name': result.get('name', trailhead['name']),
                            'lat': geometry.get('lat'),
                            'lon': geometry.get('lng'),
                            'place_id': trailhead['place_id']
                        })
                except Exception as e:
                    logger.error(f"Failed to get location for {trailhead['name']}: {e}")
        
        return locations
    
    def store_raw_reviews(self, wildlife_events: List[Dict[str, Any]], db_connection: Any):
        """
        Store raw reviews in the temporary table and wildlife events in permanent table.
        This would be called by your data pipeline after scraping.
        
        Args:
            wildlife_events: List of wildlife events with raw review data
            db_connection: Database connection
        """
        cursor = db_connection.cursor()
        
        try:
            for event in wildlife_events:
                # Store raw review (30-day retention)
                cursor.execute("""
                    INSERT INTO google_reviews_raw (place_id, review_id, review_data, processed)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (place_id, review_id) DO UPDATE
                    SET review_data = EXCLUDED.review_data,
                        fetched_at = NOW()
                """, (
                    event['place_id'],
                    event['review_id'],
                    json.dumps(event.pop('raw_review_data')),  # Remove raw data from event
                    True
                ))
                
                # Store wildlife event (permanent)
                cursor.execute("""
                    INSERT INTO wildlife_events (
                        place_id, species, event_date, review_date,
                        source, confidence_score, gmu_unit, location_details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    event['place_id'],
                    event['species'],
                    event['event_date'],
                    event['review_date'],
                    event['source'],
                    event['confidence_score'],
                    event['gmu_unit'],
                    json.dumps(event['location_details'])
                ))
            
            db_connection.commit()
            logger.info(f"Stored {len(wildlife_events)} wildlife events from Google reviews")
            
        except Exception as e:
            db_connection.rollback()
            logger.error(f"Failed to store Google review data: {e}")
            raise
        finally:
            cursor.close()
