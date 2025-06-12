"""
Base scraper class with common functionality for all wildlife sighting scrapers.
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import requests
from bs4 import BeautifulSoup
from loguru import logger

class BaseScraper(ABC):
    """
    Abstract base class for all wildlife sighting scrapers.
    Provides rate limiting, error handling, and common extraction methods.
    """
    
    def __init__(self, source_name: str, rate_limit: float = 1.0):
        """
        Initialize the base scraper.
        
        Args:
            source_name: Name of the data source (e.g., '14ers', 'reddit')
            rate_limit: Seconds to wait between requests
        """
        self.source_name = source_name
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Hunting Sightings Bot 1.0; Contact: patrg444@gmail.com)'
        })
        
        # Game species keywords
        self.game_species = {
            'elk': ['elk', 'bull', 'cow', 'wapiti', 'bugle', 'bugling'],
            'deer': ['deer', 'buck', 'doe', 'muley', 'mule deer', 'whitetail', 'white-tail'],
            'bear': ['bear', 'black bear', 'griz', 'grizzly', 'bruin'],
            'pronghorn': ['pronghorn', 'antelope', 'speed goat'],
            'bighorn_sheep': ['bighorn', 'sheep', 'ram', 'ewe'],
            'mountain_goat': ['mountain goat', 'goat', 'billy', 'nanny']
        }
        
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make an HTTP request with rate limiting and error handling.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            Response object or None if request failed
        """
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _extract_sightings_from_text(self, text: str, url: str) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from text using keyword matching.
        
        Args:
            text: Text to search for sightings
            url: Source URL for attribution
            
        Returns:
            List of sighting dictionaries
        """
        import re
        
        sightings = []
        text_lower = text.lower()
        
        for species, keywords in self.game_species.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Use word boundary regex to match whole words only
                # \b ensures we match word boundaries
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                
                for match in re.finditer(pattern, text_lower):
                    index = match.start()
                    
                    # Extract 100-character window around keyword for better context
                    start = max(0, index - 50)
                    end = min(len(text), index + len(keyword) + 50)
                    context = text[start:end].strip()
                    
                    # Validate it's a real sighting mention
                    if self._validate_sighting_context(context, keyword):
                        sightings.append({
                            'species': species,
                            'raw_text': context,
                            'keyword_matched': keyword,
                            'source_url': url,
                            'source_type': self.source_name,
                            'extracted_at': datetime.utcnow()
                        })
        
        return sightings
    
    def _extract_potential_wildlife_mentions(self, text: str, url: str) -> List[Dict[str, Any]]:
        """
        Simplified extraction - just find posts mentioning wildlife species.
        Let LLM decide if it's an actual sighting.
        
        Args:
            text: Full text to analyze
            url: Source URL
            
        Returns:
            List of potential wildlife mentions for LLM validation
        """
        import re
        
        mentions = []
        text_lower = text.lower()
        
        # Check if any wildlife species are mentioned
        species_found = set()
        for species, keywords in self.game_species.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    species_found.add(species)
                    break
        
        # If wildlife mentioned, return the full text for LLM analysis
        if species_found:
            mentions.append({
                'full_text': text[:1500],  # Send up to 1500 chars
                'species_mentioned': list(species_found),
                'source_url': url,
                'source_type': self.source_name,
                'extracted_at': datetime.utcnow()
            })
        
        return mentions
    
    def _validate_sighting_context(self, context: str, keyword: str) -> bool:
        """
        Validate that the context represents a real sighting.
        
        Args:
            context: Text context around the keyword
            keyword: The matched keyword
            
        Returns:
            True if this appears to be a valid sighting
        """
        # Exclude common false positives
        false_positive_phrases = [
            'no sign of',
            'didn\'t see any',
            'no wildlife',
            'hope to see',
            'looking for',
            'wish i saw',
            'wanted to see',
            'elk mountain',  # Place names
            'deer creek',
            'bear lake',
            'goat rocks',
            'sheep mountain',
            'antelope canyon',
            'ram\'s head',  # Gear/equipment
            'deer valley',
            'elk ridge',
            'bear canyon',
            'goat trail',
            'no animals',
            'didn\'t spot',
            'failed to see',
            'gear',  # Common gear discussions
            'weight',
            'pack',
            'equipment'
        ]
        
        context_lower = context.lower()
        
        # Check for false positive phrases
        for phrase in false_positive_phrases:
            if phrase in context_lower:
                return False
        
        # Look for positive indicators - require at least one
        positive_indicators = [
            'saw', 'spotted', 'encountered', 'came across',
            'watched', 'found', 'ran into', 'crossing',
            'grazing', 'feeding', 'bedded', 'tracks',
            'sighting', 'observed', 'startled', 'spooked',
            'jumped', 'flushed', 'viewing', 'herd of',
            'group of', 'fresh sign', 'droppings', 'scat',
            'wandered', 'appeared', 'emerged', 'approached'
        ]
        
        has_positive_indicator = False
        for indicator in positive_indicators:
            if indicator in context_lower:
                has_positive_indicator = True
                break
        
        # Also check for patterns like "X elk", "X deer" (number + animal)
        import re
        # Check if there's a number before the keyword (within 10 characters)
        keyword_index = context_lower.find(keyword.lower())
        if keyword_index > 0:
            before_keyword = context_lower[max(0, keyword_index-10):keyword_index]
            if re.search(r'\b\d+\s*$', before_keyword):
                has_positive_indicator = True
        
        # Require positive indicator for validation
        return has_positive_indicator
    
    @abstractmethod
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape sightings from the data source.
        
        Args:
            lookback_days: Number of days to look back for content
            
        Returns:
            List of sighting dictionaries
        """
        pass
    
    @abstractmethod
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Get trail location data for this source.
        
        Returns:
            List of trail dictionaries with name, lat, lon
        """
        pass
