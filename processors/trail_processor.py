"""
Trail processor for aggregating and processing trail location data.
Maps trails to GMUs and provides location lookup functionality.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from loguru import logger


class TrailProcessor:
    """
    Handles trail data aggregation and processing from multiple sources.
    """
    
    def __init__(self, trail_data_path: str = "data/trails/colorado_trails.json"):
        """
        Initialize the trail processor.
        
        Args:
            trail_data_path: Path to store/load aggregated trail data
        """
        self.trail_data_path = Path(trail_data_path)
        self.trails = []
        self.trail_index = {}  # name -> trail data for quick lookup
        
    def add_trail(self, trail_data: Dict) -> None:
        """
        Add a trail to the collection.
        
        Args:
            trail_data: Dict containing trail information
                Required: name, lat, lon, source
                Optional: elevation, difficulty, gmu_units
        """
        required_fields = ['name', 'lat', 'lon', 'source']
        if not all(field in trail_data for field in required_fields):
            raise ValueError(f"Trail data must contain: {required_fields}")
        
        # Normalize trail name for indexing
        normalized_name = self._normalize_trail_name(trail_data['name'])
        
        # Add to collection
        self.trails.append(trail_data)
        self.trail_index[normalized_name] = trail_data
        
    def _normalize_trail_name(self, name: str) -> str:
        """
        Normalize trail name for consistent indexing.
        
        Args:
            name: Original trail name
            
        Returns:
            Normalized name (lowercase, no special chars)
        """
        return name.lower().strip().replace("'", "").replace("-", " ")
    
    def find_trail_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a trail by name (fuzzy matching).
        
        Args:
            name: Trail name to search for
            
        Returns:
            Trail data dict or None if not found
        """
        normalized = self._normalize_trail_name(name)
        
        # Exact match
        if normalized in self.trail_index:
            return self.trail_index[normalized]
        
        # Partial match
        for trail_name, trail_data in self.trail_index.items():
            if normalized in trail_name or trail_name in normalized:
                return trail_data
        
        return None
    
    def aggregate_14ers_trails(self, data_path: str = "data/raw/14ers_peaks.json") -> int:
        """
        Aggregate trail data from 14ers.com peak list.
        
        Args:
            data_path: Path to 14ers peak data
            
        Returns:
            Number of trails added
        """
        # Sample 14ers data (in practice, this would be scraped)
        sample_14ers = [
            {
                "name": "Mount Elbert",
                "lat": 39.1178,
                "lon": -106.4453,
                "elevation": 14440
            },
            {
                "name": "Mount Massive",
                "lat": 39.1875,
                "lon": -106.4757,
                "elevation": 14428
            },
            {
                "name": "Mount Harvard",
                "lat": 38.9244,
                "lon": -106.3208,
                "elevation": 14421
            },
            {
                "name": "Blanca Peak",
                "lat": 37.5775,
                "lon": -105.4856,
                "elevation": 14351
            },
            {
                "name": "La Plata Peak",
                "lat": 39.0294,
                "lon": -106.4729,
                "elevation": 14343
            }
        ]
        
        count = 0
        for peak in sample_14ers:
            trail_data = {
                "name": peak["name"],
                "lat": peak["lat"],
                "lon": peak["lon"],
                "elevation": peak["elevation"],
                "source": "14ers.com",
                "trail_type": "peak"
            }
            self.add_trail(trail_data)
            count += 1
        
        logger.info(f"Added {count} trails from 14ers.com")
        return count
    
    def aggregate_summitpost_trails(self) -> int:
        """
        Aggregate trail data from SummitPost (placeholder).
        
        Returns:
            Number of trails added
        """
        # Sample SummitPost data
        sample_trails = [
            {
                "name": "Mount Evans via Summit Lake",
                "lat": 39.5883,
                "lon": -105.6438,
                "source": "summitpost.org",
                "trail_type": "route"
            },
            {
                "name": "Grays Peak Standard Route",
                "lat": 39.6339,
                "lon": -105.8169,
                "source": "summitpost.org",
                "trail_type": "route"
            }
        ]
        
        count = 0
        for trail in sample_trails:
            self.add_trail(trail)
            count += 1
        
        logger.info(f"Added {count} trails from SummitPost")
        return count
    
    def save_trail_index(self) -> None:
        """Save aggregated trail data to JSON file."""
        self.trail_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.trail_data_path, 'w') as f:
            json.dump(self.trails, f, indent=2)
        
        logger.info(f"Saved {len(self.trails)} trails to {self.trail_data_path}")
    
    def load_trail_index(self) -> None:
        """Load trail data from JSON file."""
        if not self.trail_data_path.exists():
            logger.warning(f"Trail index file not found: {self.trail_data_path}")
            return
        
        with open(self.trail_data_path, 'r') as f:
            self.trails = json.load(f)
        
        # Rebuild index
        self.trail_index = {}
        for trail in self.trails:
            normalized_name = self._normalize_trail_name(trail['name'])
            self.trail_index[normalized_name] = trail
        
        logger.info(f"Loaded {len(self.trails)} trails from {self.trail_data_path}")
    
    def export_to_csv(self, output_path: str) -> None:
        """
        Export trail data to CSV format.
        
        Args:
            output_path: Path for CSV output
        """
        if not self.trails:
            logger.warning("No trails to export")
            return
        
        df = pd.DataFrame(self.trails)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(self.trails)} trails to {output_path}")
    
    def map_trails_to_gmus(self, gmu_processor) -> None:
        """
        Map trails to their corresponding GMUs.
        
        Args:
            gmu_processor: GMUProcessor instance with loaded GMU data
        """
        for trail in self.trails:
            if 'lat' in trail and 'lon' in trail:
                gmu = gmu_processor.find_gmu_for_point(trail['lat'], trail['lon'])
                if gmu:
                    trail['gmu_units'] = [gmu]
                else:
                    trail['gmu_units'] = []
        
        logger.info("Mapped trails to GMUs")
    
    def get_trails_by_gmu(self, gmu_id: str) -> List[Dict]:
        """
        Get all trails within a specific GMU.
        
        Args:
            gmu_id: GMU unit ID
            
        Returns:
            List of trail dictionaries
        """
        trails_in_gmu = []
        
        for trail in self.trails:
            if 'gmu_units' in trail and gmu_id in trail.get('gmu_units', []):
                trails_in_gmu.append(trail)
        
        return trails_in_gmu
    
    def get_trail_stats(self) -> Dict:
        """
        Get statistics about the trail collection.
        
        Returns:
            Dict with trail statistics
        """
        stats = {
            'total_trails': len(self.trails),
            'sources': {},
            'trail_types': {},
            'gmus_covered': set()
        }
        
        for trail in self.trails:
            # Count by source
            source = trail.get('source', 'unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
            
            # Count by type
            trail_type = trail.get('trail_type', 'unknown')
            stats['trail_types'][trail_type] = stats['trail_types'].get(trail_type, 0) + 1
            
            # Collect GMUs
            for gmu in trail.get('gmu_units', []):
                stats['gmus_covered'].add(gmu)
        
        stats['gmus_covered'] = list(stats['gmus_covered'])
        return stats
