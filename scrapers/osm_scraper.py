"""
OpenStreetMap scraper for Colorado trails and peaks using Overpass API.
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from loguru import logger
from .base import BaseScraper


class OSMScraper(BaseScraper):
    """
    Scraper for OpenStreetMap trails and peaks in Colorado.
    """
    
    def __init__(self):
        super().__init__(source_name="osm", rate_limit=1.0)
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.cache_path = Path("data/raw/osm_colorado_raw.json")
        
        # Overpass QL query for Colorado trails and peaks
        self.query = """
[out:json][timeout:1200];
area["ISO3166-2"="US-CO"]->.searchArea;
(
  way["highway"="path"](area.searchArea);
  relation["route"="hiking"](area.searchArea);
  node["natural"="peak"](area.searchArea);
);
out center tags;
"""
    
    def scrape(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape trails and peaks from OpenStreetMap.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            List of trail/peak dictionaries with name, lat, lon
        """
        # Check cache first
        if use_cache and self.cache_path.exists():
            logger.info("Loading OSM data from cache")
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
        else:
            logger.info("Fetching OSM data from Overpass API (this may take 2-3 minutes)")
            data = self._fetch_from_overpass()
            
            # Cache the raw response
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached raw OSM data to {self.cache_path}")
        
        # Process the data
        return self._process_osm_data(data)
    
    def _fetch_from_overpass(self) -> Dict[str, Any]:
        """
        Fetch data from Overpass API.
        
        Returns:
            Raw JSON response from Overpass
        """
        headers = {
            "User-Agent": "Hunting-Sightings-Channel/1.0 (contact@example.com)"
        }
        
        # Make the request with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.overpass_url,
                    data={"data": self.query},
                    headers=headers,
                    timeout=1200  # 20 minute timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retry
                else:
                    raise
    
    def _process_osm_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process raw OSM data into structured format.
        
        Args:
            data: Raw JSON from Overpass API
            
        Returns:
            List of trail/peak dictionaries
        """
        results = []
        elements = data.get("elements", [])
        
        logger.info(f"Processing {len(elements)} OSM elements")
        
        for element in elements:
            # Skip elements without names
            name = element.get("tags", {}).get("name")
            if not name:
                continue
            
            # Extract coordinates
            if element["type"] == "node":
                # Direct coordinates for nodes (peaks)
                lat = element.get("lat")
                lon = element.get("lon")
                feature_type = "peak"
            else:
                # Center coordinates for ways/relations (trails)
                center = element.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")
                feature_type = "trail"
            
            if lat is None or lon is None:
                continue
            
            # Extract additional tags
            tags = element.get("tags", {})
            elevation = tags.get("ele")  # Elevation if available
            
            results.append({
                "name": name,
                "lat": lat,
                "lon": lon,
                "type": feature_type,
                "elevation": elevation,
                "osm_id": element.get("id"),
                "osm_type": element.get("type"),
                "source": "openstreetmap"
            })
        
        logger.info(f"Found {len(results)} named trails and peaks")
        return results
    
    def save_to_csv(self, data: List[Dict[str, Any]], output_path: str = "data/trails/colorado_trails_peaks.csv"):
        """
        Save processed data to CSV.
        
        Args:
            data: List of trail/peak dictionaries
            output_path: Path to save CSV
        """
        df = pd.DataFrame(data)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} trails and peaks to {output_path}")
        
        return df
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Get trail locations for compatibility with base scraper.
        
        Returns:
            List of trail dictionaries
        """
        data = self.scrape()
        return [d for d in data if d["type"] == "trail"]
