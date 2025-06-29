#!/usr/bin/env python3
"""
Analyze the accuracy of nano model's incorrect coordinates.
"""
import json
import math
from typing import List, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in miles."""
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def analyze_accuracy():
    """Analyze nano model's coordinate accuracy."""
    
    # Load the comparison results
    with open('model_comparison_20250629_070140.json', 'r') as f:
        data = json.load(f)
    
    # Find nano results
    nano_results = None
    for result in data['results']:
        if 'nano' in result['model']:
            nano_results = result
            break
    
    if not nano_results:
        print("No nano results found")
        return
    
    print("GPT-4.1 Nano Coordinate Accuracy Analysis")
    print("=" * 60)
    
    incorrect_coords = []
    coords_when_null_expected = []
    
    for detail in nano_results['details']:
        if detail['status'].startswith('✗ Incorrect'):
            incorrect_coords.append(detail)
        elif detail['status'] == '⚠ Coords when null expected':
            coords_when_null_expected.append(detail)
    
    print(f"\nTotal incorrect coordinates: {len(incorrect_coords)}")
    print(f"Coordinates provided when null expected: {len(coords_when_null_expected)}")
    
    print("\n--- INCORRECT COORDINATES ANALYSIS ---")
    for item in incorrect_coords:
        location = item['location']
        extracted = item['extracted']
        expected = item['expected']
        
        if extracted and expected:
            lat_diff = abs(extracted[0] - expected[0])
            lon_diff = abs(extracted[1] - expected[1])
            
            # Calculate distance in miles
            distance = haversine_distance(expected[0], expected[1], extracted[0], extracted[1])
            
            print(f"\n{location}:")
            print(f"  Expected: {expected}")
            print(f"  Extracted: {extracted}")
            print(f"  Lat difference: {lat_diff:.4f}° ({lat_diff * 69:.1f} miles)")
            print(f"  Lon difference: {lon_diff:.4f}° ({lon_diff * 54:.1f} miles at this latitude)")
            print(f"  Direct distance: {distance:.1f} miles")
    
    print("\n--- COORDINATES FOR VAGUE LOCATIONS ---")
    for item in coords_when_null_expected:
        location = item['location']
        extracted = item['extracted']
        
        print(f"\n{location}:")
        print(f"  Extracted: {extracted}")
        print(f"  Note: This location is too vague to have specific coordinates")
    
    # Calculate average error for incorrect coordinates
    if incorrect_coords:
        total_distance = 0
        for item in incorrect_coords:
            if item['extracted'] and item['expected']:
                distance = haversine_distance(
                    item['expected'][0], item['expected'][1],
                    item['extracted'][0], item['extracted'][1]
                )
                total_distance += distance
        
        avg_distance = total_distance / len(incorrect_coords)
        print(f"\n--- SUMMARY ---")
        print(f"Average error distance for incorrect coordinates: {avg_distance:.1f} miles")
        
        # Check if errors are reasonable for hunting purposes
        print(f"\nFor hunting context:")
        print(f"- GMU (Game Management Unit) size: typically 100-500 square miles")
        print(f"- Average error of {avg_distance:.1f} miles is {'ACCEPTABLE' if avg_distance < 20 else 'CONCERNING'} for GMU-level accuracy")

if __name__ == "__main__":
    analyze_accuracy()