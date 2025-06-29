#!/usr/bin/env python3
"""Test if the LLM validator now extracts coordinates."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.llm_validator import LLMValidator
import json

def test_llm_coordinates():
    """Test coordinate extraction from location names."""
    
    validator = LLMValidator()
    
    # Test cases with known Colorado locations
    test_cases = [
        {
            'text': "Saw a huge bull elk this morning at Bear Lake in Rocky Mountain National Park. Beautiful sunrise!",
            'species': 'elk'
        },
        {
            'text': "Black bear sighting near the Maroon Bells yesterday. Keep your distance!",
            'species': 'bear'
        },
        {
            'text': "Mountain goats spotted on Mount Evans summit. Amazing to see them up close.",
            'species': 'mountain goat'
        },
        {
            'text': "Deer everywhere in downtown Estes Park this evening. Must have seen 20+.",
            'species': 'deer'
        }
    ]
    
    print("Testing LLM coordinate extraction...\n")
    
    for i, test in enumerate(test_cases):
        print(f"Test {i+1}: {test['species']}")
        print(f"Text: {test['text'][:100]}...")
        
        # Analyze with LLM
        result = validator.analyze_full_text_for_sighting(
            test['text'],
            test['species'],
            'test_subreddit'
        )
        
        if result:
            print(f"✓ Location: {result.get('location_name')}")
            if result.get('coordinates'):
                print(f"✓ Coordinates: {result['coordinates']}")
            else:
                print("✗ No coordinates extracted")
            print(f"✓ Radius: {result.get('location_confidence_radius')} miles")
        else:
            print("✗ No result from LLM")
        
        print("-" * 50)
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_llm_coordinates()