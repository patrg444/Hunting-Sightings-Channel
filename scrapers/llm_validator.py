"""
LLM-based validation for wildlife sightings with caching support.
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from loguru import logger

# OpenAI will be optional - fallback to keyword validation if not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - wildlife validation will use keyword matching only")


class LLMValidator:
    """
    Validates wildlife sightings using LLM with caching to reduce API costs.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "parsed_posts.json"
        self.cache = self._load_cache()
        
        # Rate limiting
        self.last_api_call = 0
        self.min_time_between_calls = 20.5  # 20.5 seconds between calls for 3 RPM limit
        
        # Initialize OpenAI if available
        self.llm_available = False
        self.client = None
        
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            # Clear any proxy settings that might interfere
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                         'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
            original_proxies = {}
            for var in proxy_vars:
                if var in os.environ:
                    original_proxies[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                from openai import OpenAI
                # Simple initialization with just API key
                self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                self.llm_available = True
                logger.info("LLM validation enabled with OpenAI")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.llm_available = False
            
            # Restore original proxy settings
            for var, value in original_proxies.items():
                os.environ[var] = value
        else:
            self.llm_available = False
            if OPENAI_AVAILABLE:
                logger.warning("OpenAI available but no API key found in environment")
    
    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_content_hash(self, content: str) -> str:
        """Generate hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def should_process_post(self, post_id: str, content: str, max_age_days: int = 30) -> bool:
        """
        Check if a post needs processing.
        
        Args:
            post_id: Unique identifier for the post
            content: Current content of the post
            max_age_days: Maximum age before reprocessing
            
        Returns:
            True if post should be processed
        """
        if post_id not in self.cache:
            return True
        
        cached_data = self.cache[post_id]
        
        # Check if content changed
        current_hash = self._get_content_hash(content)
        if current_hash != cached_data.get('content_hash'):
            logger.info(f"Post {post_id} content changed, needs reprocessing")
            return True
        
        # Check age
        parsed_date = datetime.fromisoformat(cached_data['parsed_date'])
        days_old = (datetime.now() - parsed_date).days
        
        if days_old > max_age_days:
            logger.info(f"Post {post_id} is {days_old} days old, needs reprocessing")
            return True
        
        return False
    
    def get_cached_sightings(self, post_id: str) -> List[Dict[str, Any]]:
        """Get cached sightings for a post."""
        if post_id in self.cache:
            return self.cache[post_id].get('sightings', [])
        return []
    
    def validate_sighting_with_llm(self, context: str, keyword: str, species: str) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Use LLM to validate if this is a real wildlife sighting AND extract location data.
        
        Args:
            context: Text context around the keyword
            keyword: The wildlife keyword found
            species: The species type
            
        Returns:
            Tuple of (is_valid, confidence_score, location_data)
        """
        if not self.llm_available:
            # Fallback to simple validation
            is_valid, confidence = self._simple_validation(context, keyword)
            return is_valid, confidence, {}
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        if time_since_last < self.min_time_between_calls:
            sleep_time = self.min_time_between_calls - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        try:
            prompt = f"""
            Analyze this text for a wildlife sighting of {species} and extract any location information.
            
            Text: "{context}"
            Wildlife keyword found: "{keyword}"
            
            Return a JSON object with:
            {{
                "is_sighting": true/false,
                "confidence": 0-100,
                "gmu_number": null or number (e.g., 12 from "GMU 12" or "unit 12"),
                "county": null or county name,
                "location_name": null or specific place (trail, peak, town, etc),
                "coordinates": null or [lat, lon] if mentioned,
                "elevation": null or elevation in feet,
                "location_description": brief description of location mentioned
            }}
            
            Examples:
            - "saw 6 elk in GMU 23 near Durango" → {{"is_sighting": true, "confidence": 95, "gmu_number": 23, "location_name": "Durango"}}
            - "planning to hunt unit 421 next year" → {{"is_sighting": false, "confidence": 98, "gmu_number": 421}}
            - "bear tracks at 11,000 feet on Mt. Elbert" → {{"is_sighting": true, "confidence": 85, "location_name": "Mt. Elbert", "elevation": 11000}}
            """
            
            self.last_api_call = time.time()
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are a wildlife sighting and location extractor. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"LLM response: {result[:200]}...")
            
            # Clean up markdown code blocks if present
            if result.startswith('```'):
                # Remove markdown code blocks
                result = result.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON response
            data = json.loads(result)
            is_valid = data.get('is_sighting', False)
            confidence = data.get('confidence', 50) / 100.0
            
            # Extract location data
            location_data = {
                'gmu_number': data.get('gmu_number'),
                'county': data.get('county'),
                'location_name': data.get('location_name'),
                'coordinates': data.get('coordinates'),
                'elevation': data.get('elevation'),
                'location_description': data.get('location_description')
            }
            
            # Remove None values
            location_data = {k: v for k, v in location_data.items() if v is not None}
            
            return is_valid, confidence, location_data
            
        except Exception as e:
            logger.error(f"LLM validation/location extraction failed: {e}")
        
        # Fallback to simple validation
        is_valid, confidence = self._simple_validation(context, keyword)
        return is_valid, confidence, {}
    
    def analyze_full_text_for_sighting(self, full_text: str, species_mentioned: List[str]) -> Optional[Dict[str, Any]]:
        """
        Analyze full post/comment text to determine if it contains wildlife sightings and extract location data.
        More comprehensive than the snippet-based validation.
        
        Args:
            full_text: Complete text to analyze
            species_mentioned: List of species found in the text
            
        Returns:
            Sighting details with location data if found, None otherwise
        """
        if not self.llm_available:
            # Can't do full analysis without LLM
            return None
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        if time_since_last < self.min_time_between_calls:
            sleep_time = self.min_time_between_calls - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        try:
            prompt = f"""
            Analyze this Reddit post/comment for wildlife sightings in Colorado and extract location information.

            Text: "{full_text[:1500]}"  # Limit to 1500 chars to avoid token limits
            
            Species mentioned: {', '.join(species_mentioned)}

            Return a JSON object with:
            {{
                "is_sighting": true/false (actual encounter, not plans/wishes),
                "species": primary species if sighting,
                "confidence": 0-100,
                "gmu_number": null or number (e.g., 12 from "GMU 12" or "unit 12"),
                "county": null or Colorado county name,
                "location_name": null or specific place (trail, peak, town),
                "coordinates": ALWAYS provide [lat, lon] - use your best estimate based on location description,
                "elevation": null or elevation in feet,
                "location_description": brief location summary
            }}
            
            IMPORTANT: Always provide coordinates as [latitude, longitude] based on:
            - Exact coordinates if mentioned
            - Known Colorado landmarks (peaks, lakes, towns, trails)
            - GMU center points:
              GMU 1: [40.6961, -108.9841], GMU 2: [40.7484, -108.521], GMU 3: [40.358, -108.421]
              GMU 11: [40.1766, -108.3343], GMU 12: [40.0745, -108.119], GMU 13: [39.9202, -108.1033]
              GMU 21: [40.0196, -107.8346], GMU 22: [39.8639, -107.7726], GMU 23: [39.7137, -107.8096]
              GMU 35: [39.4972, -106.8516], GMU 36: [39.3938, -106.4761], GMU 37: [39.6282, -106.2476]
              GMU 38: [39.7316, -106.074], GMU 39: [39.9253, -105.871], GMU 371: [39.5245, -106.2819]
              GMU 471: [39.2765, -106.3736], GMU 49: [39.168, -105.8966], GMU 50: [39.5316, -105.8236]
              GMU 500: [39.6501, -105.5957], GMU 501: [39.3891, -105.4788], GMU 51: [39.1668, -105.5821]
              GMU 511: [38.7991, -105.4737], GMU 512: [38.4516, -105.4322], GMU 52: [38.9485, -105.0881]
              GMU 521: [38.3853, -105.1021], GMU 53: [37.8915, -106.7966], GMU 54: [37.7513, -106.4653]
              GMU 55: [38.0604, -106.2319], GMU 551: [37.7988, -106.1128], GMU 56: [38.5313, -106.2113]
              GMU 561: [38.249, -106.2252], GMU 57: [38.8283, -105.9357], GMU 58: [38.8627, -105.6616]
              GMU 581: [38.5906, -105.5926], GMU 59: [38.4982, -105.2814], GMU 591: [38.1885, -105.3286]
            - General area descriptions (e.g., "near Denver" = [39.7392, -104.9903])
            - If no location info, use Colorado center [39.5501, -105.7821]
            
            Consider hunting success ("got my elk", "tagged out", "harvested") as valid sightings.
            Also consider trail cam photos, hunting encounters, tracks/sign if fresh, and any actual wildlife observations.
            Be inclusive - if someone mentions seeing wildlife, it's likely a sighting unless they explicitly say they didn't see it.
            
            Examples:
            - "Finally got my bull elk in unit 12 near Durango" → {{"is_sighting": true, "species": "elk", "confidence": 95, "gmu_number": 12, "location_name": "Durango", "coordinates": [40.0745, -108.119]}}
            - "Saw 6 deer at 10,500 feet on the Maroon Bells trail" → {{"is_sighting": true, "species": "deer", "confidence": 90, "elevation": 10500, "location_name": "Maroon Bells trail", "coordinates": [39.0708, -106.9889]}}
            - "Bear spotted near Estes Park" → {{"is_sighting": true, "species": "bear", "confidence": 85, "location_name": "Estes Park", "coordinates": [40.3773, -105.5217]}}
            - "Planning to hunt elk next season" → {{"is_sighting": false, "confidence": 98}}
            """
            
            self.last_api_call = time.time()
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are a wildlife sighting and location extractor for Colorado hunting/outdoor forums. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"LLM response: {result[:200]}...")
            
            # Clean up markdown code blocks if present
            if result.startswith('```'):
                # Remove markdown code blocks
                result = result.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON response
            data = json.loads(result)
            
            if data.get('is_sighting', False):
                # Build response with location data
                sighting_data = {
                    'is_sighting': True,
                    'species': data.get('species', species_mentioned[0] if species_mentioned else 'unknown'),
                    'confidence': data.get('confidence', 50) / 100.0,
                    'llm_analyzed': True
                }
                
                # Add location fields if present
                location_fields = ['gmu_number', 'county', 'location_name', 'coordinates', 'elevation', 'location_description']
                for field in location_fields:
                    if data.get(field) is not None:
                        sighting_data[field] = data[field]
                
                return sighting_data
            
            return None
            
        except Exception as e:
            logger.error(f"Full text LLM analysis failed: {e}")
            if 'result' in locals():
                logger.error(f"Raw LLM response was: {result}")
            return None
    
    def _simple_validation(self, context: str, keyword: str) -> Tuple[bool, float]:
        """
        Simple rule-based validation as fallback.
        """
        context_lower = context.lower()
        
        # Strong positive indicators
        strong_positive_words = ['saw', 'spotted', 'encountered', 'watched', 'observed', 'found']
        has_strong_positive = any(word in context_lower for word in strong_positive_words)
        
        # Moderate positive indicators
        moderate_positive_words = ['tracks', 'sign', 'scat', 'herd of', 'group of']
        has_moderate_positive = any(word in context_lower for word in moderate_positive_words)
        
        # Check for number + animal pattern (e.g., "6 mountain goats")
        import re
        number_pattern = r'\b\d+\s*' + re.escape(keyword.lower())
        has_number_pattern = bool(re.search(number_pattern, context_lower))
        
        # Strong negative indicators (place names)
        place_name_indicators = []
        if keyword.lower() in ['bear', 'elk', 'deer', 'goat', 'sheep']:
            place_name_indicators = [
                f'{keyword.lower()} lake',
                f'{keyword.lower()} creek', 
                f'{keyword.lower()} trail',
                f'{keyword.lower()} mountain',
                f'{keyword.lower()} ridge',
                f'{keyword.lower()} canyon'
            ]
        
        is_place_name = any(place in context_lower for place in place_name_indicators)
        
        # Other negative indicators
        negative_phrases = ['looking for', 'hope to see', 'planning', 'resistant', 'proof']
        has_negative = any(phrase in context_lower for phrase in negative_phrases)
        
        # Decision logic
        if is_place_name or has_negative:
            return False, 0.8
        elif has_strong_positive:
            return True, 0.8
        elif has_moderate_positive or has_number_pattern:
            return True, 0.7
        else:
            # Default to false for safety
            return False, 0.5
    
    def validate_sightings_batch(self, sightings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate multiple sightings and extract location data, using cache where possible.
        
        Args:
            sightings: List of potential sightings to validate
            
        Returns:
            List of validated sightings with confidence scores and location data
        """
        validated = []
        
        for sighting in sightings:
            is_valid, confidence, location_data = self.validate_sighting_with_llm(
                sighting['raw_text'],
                sighting['keyword_matched'],
                sighting['species']
            )
            
            if is_valid and confidence > 0.7:  # Configurable threshold
                sighting['llm_validated'] = True
                sighting['confidence'] = confidence
                
                # Add location data to sighting
                if location_data:
                    sighting.update(location_data)
                
                validated.append(sighting)
            
        return validated
    
    def update_cache(self, post_id: str, content: str, sightings: List[Dict[str, Any]], 
                     source: str = "reddit"):
        """
        Update cache with processed post data.
        
        Args:
            post_id: Unique identifier for the post
            content: Content that was processed
            sightings: Validated sightings found
            source: Source platform
        """
        self.cache[post_id] = {
            'parsed_date': datetime.now().isoformat(),
            'content_hash': self._get_content_hash(content),
            'source': source,
            'has_sightings': len(sightings) > 0,
            'sighting_count': len(sightings),
            'sightings': sightings
        }
        
        self._save_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache."""
        total_posts = len(self.cache)
        posts_with_sightings = sum(1 for p in self.cache.values() if p['has_sightings'])
        total_sightings = sum(p['sighting_count'] for p in self.cache.values())
        
        return {
            'total_posts_cached': total_posts,
            'posts_with_sightings': posts_with_sightings,
            'total_sightings': total_sightings,
            'cache_file': str(self.cache_file)
        }
