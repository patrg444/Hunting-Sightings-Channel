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
    
    def __init__(self, cache_dir: str = None):
        # Use /tmp for Lambda, local data/cache otherwise
        if cache_dir is None:
            cache_dir = "/tmp/cache" if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else "data/cache"
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
                self.model = "gpt-4.1-nano-2025-04-14"  # Faster model with good accuracy
                logger.info(f"LLM validation enabled with OpenAI using model: {self.model}")
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
        """Generate hash of content for change detection.
        DEPRECATED: Kept for backward compatibility only.
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def should_process_post(self, post_id: str, content: str, max_age_days: int = 30, 
                          post_datetime: Optional[datetime] = None, post_title: Optional[str] = None) -> bool:
        """
        Check if a post needs processing.
        
        Args:
            post_id: Unique identifier for the post
            content: Current content of the post (kept for backward compatibility)
            max_age_days: Maximum age before reprocessing
            post_datetime: The post's creation datetime
            post_title: The post's title
            
        Returns:
            True if post should be processed
        """
        if post_id not in self.cache:
            return True
        
        cached_data = self.cache[post_id]
        
        # New approach: Check datetime + title if provided
        if post_datetime and post_title:
            # Compare datetime (convert to ISO string for consistency)
            cached_datetime = cached_data.get('post_datetime')
            current_datetime = post_datetime.isoformat() if isinstance(post_datetime, datetime) else post_datetime
            
            if cached_datetime != current_datetime:
                logger.info(f"Post {post_id} datetime changed from {cached_datetime} to {current_datetime}, needs reprocessing")
                return True
            
            # Compare title
            cached_title = cached_data.get('post_title')
            if cached_title != post_title:
                logger.info(f"Post {post_id} title changed, needs reprocessing")
                return True
        else:
            # Fallback to old hash-based approach for backward compatibility
            current_hash = self._get_content_hash(content)
            if current_hash != cached_data.get('content_hash'):
                logger.info(f"Post {post_id} content changed (hash mismatch), needs reprocessing")
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
    
    def validate_sighting_with_llm(self, context: str, keyword: str, species: str, subreddit: str = None) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Use LLM to validate if this is a real wildlife sighting AND extract location data.
        
        Args:
            context: Text context around the keyword
            keyword: The wildlife keyword found
            species: The species type
            subreddit: The subreddit where this was posted (for geographical context)
            
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
            subreddit_context = f"Posted in r/{subreddit}" if subreddit else "Context unknown"
            prompt = f"""
            Analyze this text for a wildlife sighting of {species} and extract any location information.
            {subreddit_context}
            
            Text: "{context}"
            Wildlife keyword found: "{keyword}"
            
            Return a JSON object with:
            {{
                "is_sighting": true/false,
                "confidence": 0-100 (confidence this is a real wildlife sighting vs plans/wishes/place names),
                "gmu_number": null or number (e.g., 12 from "GMU 12" or "unit 12"),
                "location_name": null or specific place (trail, peak, town, etc),
                "coordinates": null or [lat, lon] if mentioned,
                "elevation": null or elevation in feet,
                "location_confidence_radius": estimated geographical area radius in miles where the sighting occurred based on location description,
                "location_description": brief description of location mentioned
            }}
            
            Examples:
            - "saw 6 elk at the trailhead parking lot" → {{"is_sighting": true, "confidence": 100, "location_name": "trailhead parking lot", "location_confidence_radius": 0.5}}
            - "bear tracks near Aspen" → {{"is_sighting": true, "confidence": 90, "location_name": "Aspen", "location_confidence_radius": 10}}
            - "elk somewhere in GMU 12" → {{"is_sighting": true, "confidence": 85, "gmu_number": 12, "location_confidence_radius": 35}}
            
            IMPORTANT: If a location name is mentioned, you MUST provide estimated coordinates:
            - "Bear Lake in RMNP" → "coordinates": [40.3845, -105.6824]
            - "Estes Park" → "coordinates": [40.3775, -105.5253]
            - "Mount Evans" → "coordinates": [39.5883, -105.6438]
            - "Maroon Bells" → "coordinates": [39.0708, -106.9890]
            - "Quandary Peak" → "coordinates": [39.3995, -106.1005]
            Always include coordinates for known Colorado locations. Use null only if location is completely unknown.
            """
            
            self.last_api_call = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a wildlife sighting and location extractor. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,  # Increased for coordinate data
                temperature=0.1
            )
            
            if not response or not response.choices:
                logger.error("Empty response from OpenAI")
                return False, 0.0, {}
                
            result = response.choices[0].message.content
            if not result:
                logger.error("Empty content in OpenAI response")
                return False, 0.0, {}
                
            result = result.strip()
            
            # Debug: log the raw response
            logger.debug(f"LLM raw response: {result[:500]}")
            
            # Extract JSON from markdown code blocks if present
            if "```json" in result:
                start = result.find("```json") + 7
                end = result.find("```", start)
                if end > start:
                    result = result[start:end].strip()
            elif "```" in result:
                # Generic code block
                start = result.find("```") + 3
                end = result.find("```", start)
                if end > start:
                    result = result[start:end].strip()
            
            # Remove comments from JSON (nano model adds them)
            import re
            result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)
            
            # Parse JSON response
            data = json.loads(result)
            is_valid = data.get('is_sighting', False)
            confidence = data.get('confidence', 50) / 100.0
            
            # Extract location data
            location_data = {
                'gmu_number': data.get('gmu_number'),
                'location_name': data.get('location_name'),
                'coordinates': data.get('coordinates'),
                'elevation': data.get('elevation'),
                'location_confidence_radius': data.get('location_confidence_radius'),
                'location_description': data.get('location_description')
            }
            
            # Debug coordinates
            if 'coordinates' in data:
                logger.debug(f"Found coordinates in LLM response: {data['coordinates']}")
            
            # Remove None values
            location_data = {k: v for k, v in location_data.items() if v is not None}
            
            return is_valid, confidence, location_data
            
        except Exception as e:
            logger.error(f"LLM validation/location extraction failed: {e}")
        
        # Fallback to simple validation
        is_valid, confidence = self._simple_validation(context, keyword)
        return is_valid, confidence, {}
    
    def analyze_full_text_for_sighting(self, full_text: str, species_mentioned: List[str], subreddit: str = None) -> Optional[Dict[str, Any]]:
        """
        Analyze full post/comment text to determine if it contains wildlife sightings and extract location data.
        More comprehensive than the snippet-based validation.
        
        Args:
            full_text: Complete text to analyze
            species_mentioned: List of species found in the text
            subreddit: The subreddit where this was posted (for geographical context)
            
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
            subreddit_context = f"Posted in r/{subreddit}" if subreddit else "Reddit post"
            prompt = f"""
            Analyze this Reddit post/comment for wildlife sightings and extract location information.
            {subreddit_context}

            Text: "{full_text[:1500]}"  # Limit to 1500 chars to avoid token limits
            
            Species mentioned: {', '.join(species_mentioned)}

            Return a JSON object with:
            {{
                "is_sighting": true/false (actual encounter, not plans/wishes),
                "species": primary species if sighting,
                "confidence": 0-100 (confidence this is a real wildlife sighting),
                "gmu_number": null or number (e.g., 12 from "GMU 12" or "unit 12"),
                "location_name": null or specific place (trail, peak, town),
                "coordinates": null or [lat, lon] if mentioned,
                "elevation": null or elevation in feet,
                "location_confidence_radius": estimated geographical area radius in miles where the sighting occurred,
                "location_description": brief location summary
            }}
            
            Consider hunting success ("got my elk", "tagged out", "harvested") as valid sightings.
            
            Examples:
            - "Finally got my bull elk in unit 12 near Durango" → {{"is_sighting": true, "species": "elk", "confidence": 95, "gmu_number": 12, "location_name": "Durango", "location_confidence_radius": 8}}
            - "Saw 6 deer at the bridge on Maroon Creek trail" → {{"is_sighting": true, "species": "deer", "confidence": 100, "location_name": "Maroon Creek trail", "location_confidence_radius": 1}}
            - "Bear tracks somewhere in GMU 39" → {{"is_sighting": true, "species": "bear", "confidence": 90, "gmu_number": 39, "location_confidence_radius": 40}}
            
            IMPORTANT: If a location name is mentioned, you MUST provide estimated coordinates:
            - "Bear Lake" → "coordinates": [40.3845, -105.6824]
            - "Estes Park" → "coordinates": [40.3775, -105.5253]
            - "Mount Evans" → "coordinates": [39.5883, -105.6438]
            - "Maroon Bells" → "coordinates": [39.0708, -106.9890]
            - "Durango" → "coordinates": [37.2753, -107.8801]
            Always include coordinates for known Colorado locations. Use null only if location is completely unknown.
            """
            
            self.last_api_call = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a wildlife sighting and location extractor for Colorado hunting/outdoor forums. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in result:
                start = result.find("```json") + 7
                end = result.find("```", start)
                if end > start:
                    result = result[start:end].strip()
            elif "```" in result:
                # Generic code block
                start = result.find("```") + 3
                end = result.find("```", start)
                if end > start:
                    result = result[start:end].strip()
            
            # Remove comments from JSON (nano model adds them)
            import re
            result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)
            
            # Parse JSON response
            data = json.loads(result)
            logger.info(f"LLM response data: {data}")
            
            if data.get('is_sighting', False):
                # Build response with location data
                sighting_data = {
                    'is_sighting': True,
                    'species': data.get('species', species_mentioned[0] if species_mentioned else 'unknown'),
                    'confidence': data.get('confidence', 50) / 100.0,
                    'llm_analyzed': True
                }
                
                # Add location fields if present
                location_fields = ['gmu_number', 'location_name', 'coordinates', 'elevation', 'location_confidence_radius', 'location_description']
                for field in location_fields:
                    if data.get(field) is not None:
                        sighting_data[field] = data[field]
                        if field == 'coordinates':
                            logger.info(f"✓ Added coordinates to sighting: {data[field]}")
                
                logger.debug(f"Returning sighting data: {sighting_data}")
                return sighting_data
            
            return None
            
        except Exception as e:
            logger.error(f"Full text LLM analysis failed: {e}")
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
    
    def validate_sightings_batch(self, sightings: List[Dict[str, Any]], subreddit: str = None) -> List[Dict[str, Any]]:
        """
        Validate multiple sightings and extract location data, using cache where possible.
        
        Args:
            sightings: List of potential sightings to validate
            subreddit: The subreddit where these were posted (for geographical context)
            
        Returns:
            List of validated sightings with confidence scores and location data
        """
        validated = []
        
        for sighting in sightings:
            is_valid, confidence, location_data = self.validate_sighting_with_llm(
                sighting['raw_text'],
                sighting['keyword_matched'],
                sighting['species'],
                subreddit
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
                     source: str = "reddit", post_datetime: Optional[datetime] = None, 
                     post_title: Optional[str] = None):
        """
        Update cache with processed post data.
        
        Args:
            post_id: Unique identifier for the post
            content: Content that was processed
            sightings: Validated sightings found
            source: Source platform
            post_datetime: The post's creation datetime
            post_title: The post's title
        """
        cache_entry = {
            'parsed_date': datetime.now().isoformat(),
            'source': source,
            'has_sightings': len(sightings) > 0,
            'sighting_count': len(sightings),
            'sightings': sightings
        }
        
        # Add new fields if provided
        if post_datetime:
            cache_entry['post_datetime'] = post_datetime.isoformat() if isinstance(post_datetime, datetime) else post_datetime
        
        if post_title:
            cache_entry['post_title'] = post_title
        
        # Keep content_hash for backward compatibility with existing cache
        cache_entry['content_hash'] = self._get_content_hash(content)
        
        self.cache[post_id] = cache_entry
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
