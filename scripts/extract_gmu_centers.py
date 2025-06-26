#!/usr/bin/env python3
"""
Extract center points of all Colorado GMUs for LLM coordinate generation.
"""

import json
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point
import numpy as np

def main():
    # Load GMU data
    gmu_file = Path("data/gmu/colorado_gmu.geojson")
    if not gmu_file.exists():
        print(f"GMU file not found: {gmu_file}")
        return
    
    gdf = gpd.read_file(gmu_file)
    
    # Extract GMU centers
    gmu_centers = {}
    
    for idx, row in gdf.iterrows():
        # Get GMU ID
        gmu_id = None
        if 'GMUID' in row:
            gmu_id = str(row['GMUID'])
        elif 'DAU' in row:
            gmu_id = str(row['DAU'])
        elif 'NAME' in row:
            # Extract number from name like "GMU 12" or "Unit 12"
            import re
            match = re.search(r'\b(\d+)\b', str(row['NAME']))
            if match:
                gmu_id = match.group(1)
        
        if gmu_id and row.geometry:
            # Get centroid
            centroid = row.geometry.centroid
            
            # Get bounds for context
            bounds = row.geometry.bounds
            
            gmu_centers[gmu_id] = {
                'center': [round(centroid.y, 4), round(centroid.x, 4)],  # [lat, lon]
                'bounds': {
                    'north': round(bounds[3], 4),
                    'south': round(bounds[1], 4),
                    'east': round(bounds[2], 4),
                    'west': round(bounds[0], 4)
                },
                'name': row.get('NAME', f'GMU {gmu_id}')
            }
    
    # Save as JSON
    output_file = Path("data/gmu_centers.json")
    with open(output_file, 'w') as f:
        json.dump(gmu_centers, f, indent=2)
    
    print(f"Extracted {len(gmu_centers)} GMU centers to {output_file}")
    
    # Print some examples for the LLM prompt
    print("\nExample GMU centers for LLM prompt:")
    for gmu_id in sorted(list(gmu_centers.keys()))[:10]:
        center = gmu_centers[gmu_id]['center']
        print(f"GMU {gmu_id}: [{center[0]}, {center[1]}]")

if __name__ == "__main__":
    main()