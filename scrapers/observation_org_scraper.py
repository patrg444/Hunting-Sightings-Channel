"""
Scraper for Observation.org (Waarneming) wildlife observations in Colorado.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from .base import BaseScraper


class ObservationOrgScraper(BaseScraper):
    """
    Scraper for Observation.org observations of game species in Colorado.
    """
    
    def __init__(self):
        super().__init__(source_name="observation_org", rate_limit=1.0)
        self.base_url = "https://waarneming.nl/api/v1"
        
        # Colorado bounding box (bbox)
        # West, South, East, North
        self.colorado_bbox = "-109.06,36.99,-102.04,41.00"
        
        # Game species names to search for
        # Observation.org uses scientific names
        self.game_species = {
            'Cervus canadensis': 'Elk',
            'Odocoileus hemionus': 'Mule Deer',
            'Odocoileus virginianus': 'White-tailed Deer',
            'Ursus americanus': 'Black Bear',
            'Puma concolor': 'Mountain Lion',
            'Ovis canadensis': 'Bighorn Sheep',
            'Oreamnos americanus': 'Mountain Goat',
            'Alces alces': 'Moose',
            'Antilocapra americana': 'Pronghorn',
            # Additional mammals sometimes hunted
            'Lynx canadensis': 'Canada Lynx',
            'Lynx rufus': 'Bobcat',
            'Canis latrans': 'Coyote',
            'Vulpes vulpes': 'Red Fox',
            'Marmota flaviventris': 'Yellow-bellied Marmot',
            'Castor canadensis': 'American Beaver',
            'Erethizon dorsatum': 'North American Porcupine'
        }
    
    def scrape(self, lookback_days: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape recent wildlife observations from Observation.org.
        
        Args:
            lookback_days: Number of days to look back for observations
            
        Returns:
            List of wildlife sightings with location, species, and time data
        """
        all_sightings = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        logger.info(f"Fetching wildlife observations from last {lookback_days} days...")
        
        # Fetch observations for the date range
        observations = self._fetch_observations(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Process each observation
        for obs in observations:
            sighting = self._process_observation(obs)
            if sighting:
                all_sightings.append(sighting)
        
        logger.info(f"Found {len(all_sightings)} wildlife observations from Observation.org")
        return all_sightings
    
    def _fetch_observations(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Fetch observations for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of raw observations
        """
        url = f"{self.base_url}/observations"
        
        params = {
            'bbox': self.colorado_bbox,
            'startdate': start_date,
            'enddate': end_date,
            'geojson': 'true',
            'limit': 1000,  # Max results per request
            'has_photo': 'true',  # Only observations with photos
            'format': 'json'
        }
        
        all_observations = []
        offset = 0
        
        while True:
            params['offset'] = offset
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Extract observations from response
                if 'features' in data:
                    observations = data['features']
                elif 'results' in data:
                    observations = data['results']
                else:
                    observations = []
                
                if not observations:
                    break
                
                # Filter for game species
                for obs in observations:
                    species_name = self._extract_species_name(obs)
                    if species_name in self.game_species:
                        all_observations.append(obs)
                
                # Check if there are more results
                if len(observations) < params['limit']:
                    break
                
                offset += params['limit']
                
                # Safety check to avoid infinite loops
                if offset > 10000:
                    logger.warning("Reached maximum offset, stopping pagination")
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching Observation.org data: {e}")
                break
        
        return all_observations
    
    def _extract_species_name(self, obs: Dict[str, Any]) -> Optional[str]:
        """
        Extract species name from observation.
        
        Args:
            obs: Raw observation data
            
        Returns:
            Scientific species name or None
        """
        # Try different possible locations for species info
        if 'properties' in obs:
            props = obs['properties']
            return (props.get('species', {}).get('scientific_name') or 
                    props.get('scientific_name') or
                    props.get('name_scientific'))
        elif 'species' in obs:
            return obs['species'].get('scientific_name')
        return None
    
    def _process_observation(self, obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single observation into our sighting format.
        
        Args:
            obs: Raw observation from Observation.org API
            
        Returns:
            Processed sighting dictionary or None if invalid
        """
        try:
            # Extract coordinates
            coords = None
            if 'geometry' in obs and obs['geometry'].get('type') == 'Point':
                coords = obs['geometry']['coordinates']
            elif 'location' in obs:
                coords = [obs['location'].get('lon'), obs['location'].get('lat')]
            
            if not coords or len(coords) < 2:
                return None
            
            lon, lat = coords[0], coords[1]
            
            # Extract properties
            props = obs.get('properties', obs)
            
            # Extract species info
            species_scientific = self._extract_species_name(obs)
            if not species_scientific or species_scientific not in self.game_species:
                return None
            
            species_common = self.game_species[species_scientific]
            
            # Extract date/time
            timestamp = props.get('timestamp', props.get('date', ''))
            if timestamp:
                try:
                    obs_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    obs_datetime = datetime.now()
            else:
                return None
            
            # Build sighting record
            sighting = {
                'species': species_common,
                'species_scientific': species_scientific,
                'location': {
                    'lat': lat,
                    'lon': lon,
                    'accuracy': props.get('accuracy'),
                    'place_guess': props.get('location_name', ''),
                },
                'observed_date': obs_datetime.strftime('%Y-%m-%d'),
                'observed_time': obs_datetime.strftime('%H:%M'),
                'observer': {
                    'username': props.get('observer', {}).get('name', 'Unknown'),
                    'name': props.get('observer', {}).get('fullname', '')
                },
                'description': props.get('notes', ''),
                'photo_url': self._get_photo_url(props),
                'quality_grade': props.get('validation_status', 'unvalidated'),
                'observation_id': props.get('id'),
                'observation_url': props.get('url'),
                'source_type': 'observation_org',
                'confidence': 0.9 if props.get('validation_status') == 'validated' else 0.7
            }
            
            return sighting
            
        except Exception as e:
            logger.error(f"Error processing Observation.org observation: {e}")
            return None
    
    def _get_photo_url(self, props: Dict[str, Any]) -> Optional[str]:
        """
        Extract photo URL from observation properties.
        
        Args:
            props: Observation properties
            
        Returns:
            Photo URL or None
        """
        # Try different possible locations for photo URL
        photos = props.get('photos', [])
        if photos and isinstance(photos, list):
            return photos[0].get('url')
        elif props.get('photo_url'):
            return props['photo_url']
        elif props.get('media', []):
            media = props['media']
            if isinstance(media, list) and media:
                return media[0].get('url')
        return None
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Observation.org doesn't provide trail data.
        
        Returns:
            Empty list
        """
        return []
