"""
Scraper for iNaturalist wildlife observations in Colorado.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from .base import BaseScraper


class INaturalistScraper(BaseScraper):
    """
    Scraper for iNaturalist observations of game species in Colorado.
    """
    
    def __init__(self):
        super().__init__(source_name="inaturalist", rate_limit=1.0)
        self.base_url = "https://api.inaturalist.org/v1"
        
        # Colorado place ID (14 is California, 34 is Colorado)
        self.colorado_place_id = 34
        
        # Game species with their scientific names
        self.game_species_taxa = {
            'elk': {'name': 'Cervus canadensis', 'taxon_id': 48514},
            'mule_deer': {'name': 'Odocoileus hemionus', 'taxon_id': 42405},
            'white_tailed_deer': {'name': 'Odocoileus virginianus', 'taxon_id': 42384},
            'black_bear': {'name': 'Ursus americanus', 'taxon_id': 41638},
            'mountain_lion': {'name': 'Puma concolor', 'taxon_id': 41954},
            'bighorn_sheep': {'name': 'Ovis canadensis', 'taxon_id': 42273},
            'mountain_goat': {'name': 'Oreamnos americanus', 'taxon_id': 42255},
            'moose': {'name': 'Alces alces', 'taxon_id': 522214},
            'pronghorn': {'name': 'Antilocapra americana', 'taxon_id': 42230}
        }
    
    def scrape(self, lookback_days: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape recent wildlife observations from iNaturalist.
        
        Args:
            lookback_days: Number of days to look back for observations
            
        Returns:
            List of wildlife sightings with location, species, and time data
        """
        all_sightings = []
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        for species_key, species_info in self.game_species_taxa.items():
            logger.info(f"Fetching {species_info['name']} observations...")
            sightings = self._fetch_species_observations(
                species_info['taxon_id'],
                species_key,
                start_date
            )
            all_sightings.extend(sightings)
        
        logger.info(f"Found {len(all_sightings)} total observations from iNaturalist")
        return all_sightings
    
    def _fetch_species_observations(self, taxon_id: int, species_key: str, 
                                   start_date: str) -> List[Dict[str, Any]]:
        """
        Fetch observations for a specific species.
        
        Args:
            taxon_id: iNaturalist taxon ID for the species
            species_key: Our internal species key
            start_date: Start date for observations (YYYY-MM-DD)
            
        Returns:
            List of processed observations
        """
        params = {
            'taxon_id': taxon_id,
            'place_id': self.colorado_place_id,
            'd1': start_date,
            'geo': 'true',  # Must have coordinates
            'identified': 'true',  # Verified IDs only
            'quality_grade': 'research',  # High quality observations
            'per_page': 200,
            'order_by': 'observed_on'
        }
        
        url = f"{self.base_url}/observations"
        response = self._make_request(url, params=params)
        
        if not response:
            return []
        
        data = response.json()
        observations = data.get('results', [])
        
        # Process observations
        sightings = []
        for obs in observations:
            sighting = self._process_observation(obs, species_key)
            if sighting:
                sightings.append(sighting)
        
        return sightings
    
    def _process_observation(self, obs: Dict[str, Any], species_key: str) -> Optional[Dict[str, Any]]:
        """
        Process a single iNaturalist observation into our sighting format.
        
        Args:
            obs: Raw observation from iNaturalist API
            species_key: Our internal species key
            
        Returns:
            Processed sighting dictionary or None if invalid
        """
        try:
            # Extract coordinates
            if not obs.get('geojson'):
                return None
            
            coords = obs['geojson']['coordinates']
            lat = coords[1]
            lon = coords[0]
            
            # Extract datetime
            observed_on = obs.get('observed_on_string', obs.get('observed_on'))
            if not observed_on:
                return None
            
            # Parse the observation date/time
            try:
                # Try parsing with time first
                obs_datetime = datetime.fromisoformat(observed_on.replace('Z', '+00:00'))
            except:
                try:
                    # Fall back to date only
                    obs_datetime = datetime.strptime(observed_on, '%Y-%m-%d')
                except:
                    obs_datetime = datetime.now()
            
            # Build sighting record
            sighting = {
                'species': species_key.replace('_', ' ').title(),
                'location': {
                    'lat': lat,
                    'lon': lon,
                    'accuracy': obs.get('positional_accuracy'),
                    'place_guess': obs.get('place_guess', ''),
                },
                'observed_date': obs_datetime.strftime('%Y-%m-%d'),
                'observed_time': obs_datetime.strftime('%H:%M') if obs_datetime.hour != 0 else None,
                'observer': {
                    'username': obs.get('user', {}).get('login', 'Unknown'),
                    'name': obs.get('user', {}).get('name', '')
                },
                'description': obs.get('description', ''),
                'photo_url': self._get_photo_url(obs),
                'quality_grade': obs.get('quality_grade', 'casual'),
                'inaturalist_id': obs.get('id'),
                'inaturalist_url': obs.get('uri'),
                'source_type': 'inaturalist',
                'confidence': 1.0 if obs.get('quality_grade') == 'research' else 0.8
            }
            
            return sighting
            
        except Exception as e:
            logger.error(f"Error processing observation: {e}")
            return None
    
    def _get_photo_url(self, obs: Dict[str, Any]) -> Optional[str]:
        """
        Extract the best photo URL from an observation.
        
        Args:
            obs: Observation data
            
        Returns:
            Photo URL or None
        """
        photos = obs.get('photos', [])
        if photos:
            # Get medium-sized photo
            photo = photos[0]
            return photo.get('url', '').replace('square', 'medium')
        return None
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        iNaturalist doesn't provide trail data.
        
        Returns:
            Empty list
        """
        return []
