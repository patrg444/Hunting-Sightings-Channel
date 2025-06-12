#!/usr/bin/env python3
"""
Demo script to show point-to-GMU lookup functionality.
Usage: python demo_point_to_gmu.py <latitude> <longitude>
Example: python demo_point_to_gmu.py 39.7392 -105.2277
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.gmu_processor import GMUProcessor
import argparse

def main():
    parser = argparse.ArgumentParser(description="Look up GMU for a given lat/lon coordinate")
    parser.add_argument("latitude", type=float, help="Latitude (e.g., 39.7392)")
    parser.add_argument("longitude", type=float, help="Longitude (e.g., -105.2277)")
    args = parser.parse_args()
    
    # Initialize GMU processor
    print(f"Looking up GMU for coordinates: {args.latitude}, {args.longitude}")
    print("-" * 50)
    
    try:
        # Load GMU processor with full Colorado dataset
        gmu_processor = GMUProcessor(gmu_data_path="data/gmu/colorado_gmu.geojson")
        print("Loading Colorado GMU data...")
        gmu_processor.load_gmu_data()
        print(f"Loaded {len(gmu_processor.gmu_gdf)} GMU polygons")
        print()
        
        # Perform lookup
        print(f"Performing point-in-polygon lookup...")
        gmu = gmu_processor.find_gmu_for_point(args.latitude, args.longitude)
        
        if gmu:
            print(f"\nSUCCESS: Point ({args.latitude}, {args.longitude}) is in GMU {gmu}")
        else:
            print(f"\nPoint ({args.latitude}, {args.longitude}) is not within any Colorado GMU")
    
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
