"""
GMU (Game Management Unit) processor for spatial operations.
Handles loading GMU polygons and determining which GMU contains a given point.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pyproj import CRS
from loguru import logger


class GMUProcessor:
    """
    Handles GMU polygon operations including loading boundaries and point-in-polygon queries.
    """
    
    def __init__(self, gmu_data_path: str = "data/gmu/colorado_gmu.geojson"):
        """
        Initialize the GMU processor.
        
        Args:
            gmu_data_path: Path to GMU boundary data (GeoJSON or Shapefile)
        """
        self.gmu_data_path = Path(gmu_data_path)
        self.gmu_gdf = None
        self.target_gmus = []
        
    def load_gmu_data(self, target_gmus: Optional[List[str]] = None):
        """
        Load GMU boundary data from file.
        
        Args:
            target_gmus: List of GMU unit IDs to filter (e.g., ['12', '201'])
        """
        if not self.gmu_data_path.exists():
            raise FileNotFoundError(f"GMU data file not found: {self.gmu_data_path}")
        
        try:
            # Load based on file extension
            if self.gmu_data_path.suffix == '.geojson':
                self.gmu_gdf = gpd.read_file(self.gmu_data_path)
            elif self.gmu_data_path.suffix in ['.shp', '.shapefile']:
                self.gmu_gdf = gpd.read_file(self.gmu_data_path)
            else:
                raise ValueError(f"Unsupported file format: {self.gmu_data_path.suffix}")
            
            # Ensure CRS is WGS84 (EPSG:4326) for lat/lon operations
            if self.gmu_gdf.crs != CRS.from_epsg(4326):
                self.gmu_gdf = self.gmu_gdf.to_crs(epsg=4326)
            
            # Filter to target GMUs if specified
            if target_gmus:
                self.target_gmus = target_gmus
                # Assuming GMU unit ID is in a column like 'GMUID' or 'DAU'
                # This will need to be adjusted based on actual data structure
                if 'GMUID' in self.gmu_gdf.columns:
                    self.gmu_gdf = self.gmu_gdf[self.gmu_gdf['GMUID'].isin(target_gmus)]
                elif 'DAU' in self.gmu_gdf.columns:
                    self.gmu_gdf = self.gmu_gdf[self.gmu_gdf['DAU'].isin(target_gmus)]
                else:
                    logger.warning("Could not find GMU ID column for filtering")
            
            logger.info(f"Loaded {len(self.gmu_gdf)} GMU polygons")
            
        except Exception as e:
            logger.error(f"Error loading GMU data: {e}")
            raise
    
    def find_gmu_for_point(self, lat: float, lon: float) -> Optional[str]:
        """
        Find which GMU contains a given lat/lon point.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            GMU unit ID or None if point is not in any GMU
        """
        if self.gmu_gdf is None:
            raise ValueError("GMU data not loaded. Call load_gmu_data() first.")
        
        point = Point(lon, lat)  # Note: Point takes (lon, lat) not (lat, lon)
        
        # Find which polygon contains the point
        for idx, row in self.gmu_gdf.iterrows():
            if row.geometry.contains(point):
                # Return the GMU ID (adjust column name as needed)
                if 'GMUID' in row:
                    return str(row['GMUID'])
                elif 'DAU' in row:
                    return str(row['DAU'])
                else:
                    return str(idx)
        
        return None
    
    def find_gmus_for_trail(self, trail_points: List[Tuple[float, float]]) -> List[str]:
        """
        Find all GMUs that a trail passes through.
        
        Args:
            trail_points: List of (lat, lon) tuples representing trail
            
        Returns:
            List of unique GMU IDs the trail passes through
        """
        gmus = set()
        
        for lat, lon in trail_points:
            gmu = self.find_gmu_for_point(lat, lon)
            if gmu:
                gmus.add(gmu)
        
        return list(gmus)
    
    def get_gmu_bounds(self, gmu_id: str) -> Optional[Dict[str, float]]:
        """
        Get bounding box for a specific GMU.
        
        Args:
            gmu_id: GMU unit ID
            
        Returns:
            Dict with min_lat, max_lat, min_lon, max_lon
        """
        if self.gmu_gdf is None:
            raise ValueError("GMU data not loaded. Call load_gmu_data() first.")
        
        # Find the GMU
        if 'GMUID' in self.gmu_gdf.columns:
            gmu_row = self.gmu_gdf[self.gmu_gdf['GMUID'] == gmu_id]
        elif 'DAU' in self.gmu_gdf.columns:
            gmu_row = self.gmu_gdf[self.gmu_gdf['DAU'] == gmu_id]
        else:
            return None
        
        if gmu_row.empty:
            return None
        
        bounds = gmu_row.geometry.bounds.iloc[0]
        return {
            'min_lon': bounds['minx'],
            'min_lat': bounds['miny'],
            'max_lon': bounds['maxx'],
            'max_lat': bounds['maxy']
        }
    
    def export_simplified_geojson(self, output_path: str, tolerance: float = 0.001):
        """
        Export simplified GMU polygons as GeoJSON for web mapping.
        
        Args:
            output_path: Path to save simplified GeoJSON
            tolerance: Simplification tolerance (degrees)
        """
        if self.gmu_gdf is None:
            raise ValueError("GMU data not loaded. Call load_gmu_data() first.")
        
        # Create a copy and simplify geometries
        simplified = self.gmu_gdf.copy()
        simplified['geometry'] = simplified.geometry.simplify(tolerance)
        
        # Keep only essential columns
        essential_cols = ['geometry']
        if 'GMUID' in simplified.columns:
            essential_cols.append('GMUID')
        if 'DAU' in simplified.columns:
            essential_cols.append('DAU')
        if 'NAME' in simplified.columns:
            essential_cols.append('NAME')
        
        simplified = simplified[essential_cols]
        
        # Save as GeoJSON
        simplified.to_file(output_path, driver='GeoJSON')
        logger.info(f"Exported simplified GMU data to {output_path}")
    
    def download_colorado_gmu_data(self):
        """
        Download Colorado GMU data from CPW (Colorado Parks and Wildlife).
        This is a placeholder - actual implementation would download from CPW's GIS portal.
        """
        # Note: In practice, this would download from:
        # https://www.arcgis.com/home/item.html?id=190573c5aba643a0bc058e6f7f0510b7
        # or similar CPW data source
        logger.info("Colorado GMU data should be downloaded from CPW GIS portal")
        logger.info("Visit: https://cpw.state.co.us/learn/Pages/KMZ-Maps.aspx")
        
        # For now, create a sample GMU polygon for testing
        self._create_sample_gmu_data()
    
    def _create_sample_gmu_data(self):
        """Create sample GMU data for testing purposes."""
        # Sample GMU polygons for testing (approximate boundaries)
        sample_gmus = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "GMUID": "12",
                        "NAME": "GMU 12"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-105.8, 39.9],
                            [-105.5, 39.9],
                            [-105.5, 39.6],
                            [-105.8, 39.6],
                            [-105.8, 39.9]
                        ]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "GMUID": "201",
                        "NAME": "GMU 201"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-106.3, 39.7],
                            [-106.0, 39.7],
                            [-106.0, 39.4],
                            [-106.3, 39.4],
                            [-106.3, 39.7]
                        ]]
                    }
                }
            ]
        }
        
        # Save sample data
        output_path = Path("data/gmu/colorado_gmu_sample.geojson")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(sample_gmus, f, indent=2)
        
        logger.info(f"Created sample GMU data at {output_path}")
