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
        sightings = []
        text_lower = text.lower()
        
        for species, keywords in self.game_species.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                index = 0
                
                while True:
                    # Find next occurrence of keyword
                    index = text_lower.find(keyword_lower, index)
                    if index == -1:
                        break
                    
                    # Extract 50-character window around keyword
                    start = max(0, index - 25)
                    end = min(len(text), index + len(keyword) + 25)
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
                    
                    index += 1
        
        return sightings
    
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
            'elk mountain',  # Place names
            'deer creek',
            'bear lake',
            'goat rocks'
        ]
        
        context_lower = context.lower()
        for phrase in false_positive_phrases:
            if phrase in context_lower:
                return False
        
        # Look for positive indicators
        positive_indicators = [
            'saw', 'spotted', 'encountered', 'came across',
            'watched', 'found', 'ran into', 'crossing',
            'grazing', 'feeding', 'bedded', 'tracks'
        ]
        
        for indicator in positive_indicators:
            if indicator in context_lower:
                return True
        
        # Default to including it (can refine later)
        return True
    
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
