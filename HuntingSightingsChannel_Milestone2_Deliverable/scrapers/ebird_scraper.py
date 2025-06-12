"""
Scraper for eBird game bird observations in Colorado.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from .base import BaseScraper


class EBirdScraper(BaseScraper):
    """
    Scraper for eBird observations of game birds in Colorado.
    """
    
    def __init__(self):
        super().__init__(source_name="ebird", rate_limit=1.0)
        self.base_url = "https://api.ebird.org/v2"
        self.api_key = os.environ.get('EBIRD_API_KEY')
        
        if not self.api_key:
            logger.warning("EBIRD_API_KEY not found in environment variables")
        
        # Colorado region code
        self.colorado_region = "US-CO"
        
        # Game bird species codes in eBird taxonomy
        self.game_birds = {
            'wiltur': 'Wild Turkey',
            'dusgro': 'Dusky Grouse',
            'whtpta': 'White-tailed Ptarmigan',
            'rinphe': 'Ring-necked Pheasant',
            'chukur': 'Chukar',
            'grbher3': 'Great Blue Heron',  # Sometimes hunted
            'saggro': 'Greater Sage-Grouse',
            'gunnsg': 'Gunnison Sage-Grouse',
            'scaqua': 'Scaled Quail',
            'moudo': 'Mourning Dove',
            'eugdov': 'Eurasian Collared-Dove',
            # Waterfowl
            'mallar3': 'Mallard',
            'gadwal': 'Gadwall',
            'cangoo': 'Canada Goose',
            'gwfgoo': 'Greater White-fronted Goose',
            'rossgo': "Ross's Goose",
            'snogoo': 'Snow Goose',
            'pinfea': 'Northern Pintail',
            'gnwtea': 'Green-winged Teal',
            'bnwtea': 'Blue-winged Teal',
            'cintea': 'Cinnamon Teal',
            'whtduc': 'Wood Duck',
            'redhea': 'Redhead',
            'rinduc': 'Ring-necked Duck',
            'lessca': 'Lesser Scaup',
            'canvas': 'Canvasback'
        }
    
    def scrape(self, lookback_days: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape recent game bird observations from eBird.
        
        Args:
            lookback_days: Number of days to look back for observations
            
        Returns:
            List of bird sightings with location, species, and time data
        """
        if not self.api_key:
            logger.error("eBird API key not configured")
            return []
        
        all_sightings = []
        
        # Get recent observations for Colorado
        logger.info(f"Fetching game bird observations from last {lookback_days} days...")
        
        # eBird allows max 30 days lookback
        days_back = min(lookback_days, 30)
        
        # Fetch all recent observations for Colorado
        observations = self._fetch_recent_observations(days_back)
        
        # Filter for game birds
        for obs in observations:
            if obs.get('speciesCode') in self.game_birds:
                sighting = self._process_observation(obs)
                if sighting:
                    all_sightings.append(sighting)
        
        logger.info(f"Found {len(all_sightings)} game bird observations from eBird")
        return all_sightings
    
    def _fetch_recent_observations(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Fetch recent observations for Colorado.
        
        Args:
            days_back: Number of days to look back (max 30)
            
        Returns:
            List of raw observations from eBird
        """
        url = f"{self.base_url}/data/obs/{self.colorado_region}/recent"
        
        headers = {
            'X-eBirdApiToken': self.api_key
        }
        
        params = {
            'back': days_back,
            'includeProvisional': 'true',  # Include unreviewed observations
            'detail': 'full'  # Get full details
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching eBird data: {e}")
            return []
    
    def _process_observation(self, obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single eBird observation into our sighting format.
        
        Args:
            obs: Raw observation from eBird API
            
        Returns:
            Processed sighting dictionary or None if invalid
        """
        try:
            # Extract species info
            species_code = obs.get('speciesCode', '')
            species_name = self.game_birds.get(species_code, obs.get('comName', 'Unknown'))
            
            # Extract date/time
            obs_datetime = datetime.strptime(obs.get('obsDt', ''), '%Y-%m-%d %H:%M')
            
            # Build sighting record
            sighting = {
                'species': species_name,
                'location': {
                    'lat': obs.get('lat'),
                    'lon': obs.get('lng'),
                    'accuracy': None,  # eBird doesn't provide accuracy
                    'place_guess': obs.get('locName', ''),
                },
                'observed_date': obs_datetime.strftime('%Y-%m-%d'),
                'observed_time': obs_datetime.strftime('%H:%M'),
                'observer': {
                    'username': obs.get('userDisplayName', 'Unknown'),
                    'name': obs.get('userDisplayName', '')
                },
                'description': obs.get('obsComments', ''),
                'count': obs.get('howMany', 1),  # Number of birds observed
                'photo_url': None,  # eBird doesn't provide photos in this endpoint
                'quality_grade': 'reviewed' if obs.get('obsReviewed', False) else 'unreviewed',
                'ebird_checklist_id': obs.get('subId'),
                'ebird_location_id': obs.get('locId'),
                'source_type': 'ebird',
                'confidence': 0.95  # eBird data is generally high quality
            }
            
            return sighting
            
        except Exception as e:
            logger.error(f"Error processing eBird observation: {e}")
            return None
    
    def get_location_observations(self, lat: float, lon: float, radius: int = 50, 
                                 days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get observations near a specific location.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in km (max 50)
            days_back: Days to look back (max 30)
            
        Returns:
            List of observations near the location
        """
        if not self.api_key:
            logger.error("eBird API key not configured")
            return []
        
        url = f"{self.base_url}/data/obs/geo/recent"
        
        headers = {
            'X-eBirdApiToken': self.api_key
        }
        
        params = {
            'lat': lat,
            'lng': lon,
            'dist': min(radius, 50),  # Max 50km
            'back': min(days_back, 30),  # Max 30 days
            'includeProvisional': 'true',
            'detail': 'full'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            observations = response.json()
            
            # Filter for game birds
            game_bird_obs = []
            for obs in observations:
                if obs.get('speciesCode') in self.game_birds:
                    sighting = self._process_observation(obs)
                    if sighting:
                        game_bird_obs.append(sighting)
            
            return game_bird_obs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching location-based eBird data: {e}")
            return []
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        eBird doesn't provide trail data.
        
        Returns:
            Empty list
        """
        return []
