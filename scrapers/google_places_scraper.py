"""
Google Places API scraper for wildlife sightings in reviews.
Updated to return data in the same format as Reddit and 14ers scrapers.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import hashlib
import time

from .base import BaseScraper
from .llm_validator import LLMValidator


class GooglePlacesScraper(BaseScraper):
    """
    Scrapes Google Places reviews for wildlife sightings at Colorado trailheads.
    Returns data in the same format as other scrapers for consistency.
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
        return []
    
    def _extract_potential_wildlife_mentions(self, text: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract potential wildlife mentions from text."""
        mentions = []
        text_lower = text.lower()
        
        for species, keywords in self.game_species.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mentions.append({
                        'species_mentioned': species,
                        'keyword_matched': keyword,
                        'source_url': source_url,
                        'full_text': text
                    })
                    break  # Only need one keyword match per species
        
        return mentions
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Make a rate-limited request to Google Places API."""
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _fetch_place_reviews(self, place_id: str, max_reviews: int = 5) -> List[Dict[str, Any]]:
        """Fetch reviews for a specific place."""
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'reviews,name,geometry',
            'key': self.api_key
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return []
        
        try:
            data = response.json()
            if data.get('status') == 'OK':
                result = data.get('result', {})
                reviews = result.get('reviews', [])[:max_reviews]
                
                # Add place geometry to each review
                geometry = result.get('geometry', {}).get('location', {})
                for review in reviews:
                    review['place_lat'] = geometry.get('lat')
                    review['place_lng'] = geometry.get('lng')
                
                return reviews
            else:
                logger.warning(f"API returned status: {data.get('status')}")
                return []
        except Exception as e:
            logger.error(f"Failed to parse reviews: {e}")
            return []
    
    def _process_review_for_wildlife(self, review: Dict[str, Any], trailhead: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single review for wildlife mentions.
        Returns a wildlife sighting dict in the same format as Reddit/14ers scrapers.
        """
        review_text = review.get('text', '')
        if not review_text:
            return None
        
        # Check if review mentions any wildlife species
        potential_mentions = self._extract_potential_wildlife_mentions(
            review_text, 
            f"https://maps.google.com/maps/place/?q=place_id:{trailhead['place_id']}"
        )
        
        if not potential_mentions:
            return None
        
        # Process each potential mention
        for mention in potential_mentions:
            # Enhanced context for LLM
            enhanced_text = f"Review from {trailhead['name']} (Colorado trailhead): {review_text}"
            
            # Use LLM to validate and extract details
            analysis = self.llm_validator.analyze_full_text_for_sighting(
                enhanced_text,
                mention['species_mentioned'],
                'GoogleMapsReviews'  # Pass source context
            )
            
            if analysis:
                # Convert review timestamp to datetime
                review_date = datetime.fromtimestamp(review.get('time', time.time()))
                
                # Return sighting in the same format as Reddit/14ers scrapers
                sighting = {
                    # Core fields matching other scrapers
                    'species': analysis['species'],
                    'raw_text': review_text[:200] + '...' if len(review_text) > 200 else review_text,
                    'keyword_matched': mention['keyword_matched'],
                    'source_url': f"https://maps.google.com/maps/place/?q=place_id:{trailhead['place_id']}",
                    'source_type': 'google_places',
                    'extracted_at': datetime.now().isoformat(),
                    'location_name': trailhead['name'],
                    'sighting_date': review_date.isoformat(),
                    
                    # LLM validation fields
                    'confidence': analysis.get('confidence', 80),
                    'llm_validated': True,
                    'location_confidence_radius': analysis.get('location_confidence_radius'),
                    
                    # Google Places specific metadata
                    'place_id': trailhead['place_id'],
                    'place_name': trailhead['name'],
                    'review_author': review.get('author_name', 'Anonymous'),
                    'review_rating': review.get('rating'),
                    
                    # Location data
                    'latitude': review.get('place_lat') or trailhead.get('lat'),
                    'longitude': review.get('place_lng') or trailhead.get('lng'),
                    'gmu_hint': trailhead.get('gmu_hint'),
                    
                    # Additional context
                    'location_details': analysis.get('location_details', {}),
                    'full_text': review_text  # Keep full text for reference
                }
                
                # Mark review as processed in cache
                review_id = self._generate_review_id(review)
                self._mark_review_processed(review_id, trailhead['place_id'], True)
                
                return sighting
        
        # Mark review as processed even if no sighting found
        review_id = self._generate_review_id(review)
        self._mark_review_processed(review_id, trailhead['place_id'], False)
        
        return None
    
    def _generate_review_id(self, review: Dict[str, Any]) -> str:
        """Generate a unique ID for a review."""
        content = f"{review.get('author_name', '')}_{review.get('time', '')}_{review.get('text', '')[:50]}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
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
            """, (review_id, place_id, 1 if has_wildlife else 0))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not update review cache: {e}")
    
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Main scraping method that returns wildlife sightings in standard format.
        
        Args:
            lookback_days: Not used for Google Places (we get latest reviews)
            
        Returns:
            List of wildlife sighting dictionaries matching Reddit/14ers format
        """
        wildlife_sightings = []
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
                sighting = self._process_review_for_wildlife(review, trailhead)
                
                if sighting:
                    wildlife_sightings.append(sighting)
                    logger.info(f"Found {sighting['species']} sighting in Google review at {trailhead['name']}")
        
        logger.info(f"Processed {new_reviews} new reviews out of {total_reviews} total")
        logger.info(f"Found {len(wildlife_sightings)} wildlife sightings in Google reviews")
        
        return wildlife_sightings
    
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