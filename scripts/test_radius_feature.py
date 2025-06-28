#!/usr/bin/env python3
"""
Test the radius feature in LLM validator.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scrapers.llm_validator import LLMValidator
from loguru import logger

def main():
    """Test radius feature with various location descriptions."""
    logger.info("Testing radius feature in LLM validator...")
    
    validator = LLMValidator()
    
    # Test cases with varying location specificity
    test_cases = [
        {
            "text": "Trail cam caught a huge bull elk at exactly 39.4972, -106.8516 yesterday morning",
            "expected_radius": "1-2 miles (exact coordinates)"
        },
        {
            "text": "Saw 6 deer on the Maroon Bells trail near the lake at 11,000 feet",
            "expected_radius": "2-3 miles (specific trail)"
        },
        {
            "text": "Fresh bear tracks in the Hermosa Creek drainage in GMU 12",
            "expected_radius": "3-5 miles (specific drainage)"
        },
        {
            "text": "Got my elk near Durango in unit 23 last weekend",
            "expected_radius": "5-10 miles (town within GMU)"
        },
        {
            "text": "Finally tagged out on a nice buck in GMU 35",
            "expected_radius": "15-25 miles (just GMU)"
        },
        {
            "text": "Elk sighting somewhere in Colorado",
            "expected_radius": "50 miles (very vague)"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        logger.info(f"\n--- Test Case {i+1} ---")
        logger.info(f"Text: {test_case['text']}")
        logger.info(f"Expected radius: {test_case['expected_radius']}")
        
        # Analyze the text
        result = validator.analyze_full_text_for_sighting(
            test_case['text'], 
            ['elk', 'deer', 'bear']
        )
        
        if result:
            logger.info(f"✓ Detected as sighting")
            logger.info(f"  Species: {result.get('species', 'N/A')}")
            logger.info(f"  Coordinates: {result.get('coordinates', 'N/A')}")
            logger.info(f"  Radius: {result.get('radius_miles', 'N/A')} miles")
            logger.info(f"  Location: {result.get('location_name', 'N/A')}")
            logger.info(f"  GMU: {result.get('gmu_number', 'N/A')}")
        else:
            logger.warning("✗ Not detected as sighting")
        
        # Rate limiting pause
        import time
        time.sleep(1)

if __name__ == "__main__":
    main()