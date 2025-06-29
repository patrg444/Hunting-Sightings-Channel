#!/usr/bin/env python3
"""Test coordinate extraction for various location descriptions."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.llm_validator import LLMValidator

def test_coordinate_extraction():
    """Test various location descriptions."""
    
    validator = LLMValidator()
    
    test_cases = [
        {
            'text': "Saw elk near the Maroon Bells this morning",
            'species': ['elk'],
            'expected_location': 'Maroon Bells'
        },
        {
            'text': "Bear sighting in downtown Estes Park by the river",
            'species': ['bear'],
            'expected_location': 'Estes Park'
        },
        {
            'text': "Mountain goats on Mount Evans summit at 14,000 feet",
            'species': ['mountain_goat'],
            'expected_location': 'Mount Evans'
        },
        {
            'text': "Got my bull in unit 12 near Durango",
            'species': ['elk'],
            'expected_location': 'Durango'
        },
        {
            'text': "Deer everywhere on Trail Ridge Road in RMNP",
            'species': ['deer'],
            'expected_location': 'Trail Ridge Road'
        }
    ]
    
    print("Testing coordinate extraction from wildlife sightings:\n")
    
    success_count = 0
    for i, test in enumerate(test_cases):
        print(f"Test {i+1}: {test['expected_location']}")
        print(f"Text: \"{test['text']}\"")
        
        result = validator.analyze_full_text_for_sighting(
            test['text'],
            test['species'],
            'test_subreddit'
        )
        
        if result:
            location = result.get('location_name', 'Unknown')
            coords = result.get('coordinates')
            radius = result.get('location_confidence_radius', 'Unknown')
            
            print(f"  Location: {location}")
            if coords:
                print(f"  ✓ Coordinates: {coords}")
                success_count += 1
            else:
                print(f"  ✗ No coordinates")
            print(f"  Radius: {radius} miles")
        else:
            print("  ✗ No result")
        
        print("-" * 60)
    
    print(f"\nSummary: {success_count}/{len(test_cases)} successfully extracted coordinates")

if __name__ == "__main__":
    test_coordinate_extraction()