#\!/usr/bin/env python3
"""
Test LLM validator coordinate extraction.
"""

from scrapers.llm_validator import LLMValidator
from loguru import logger
import json

def test_location_extraction():
    validator = LLMValidator()
    
    test_cases = [
        {
            "text": "Saw a huge black bear near Bear Lake in RMNP today\! It was crossing the trail.",
            "keyword": "bear"
        },
        {
            "text": "6 elk spotted at the Maroon Bells trailhead parking lot this morning",
            "keyword": "elk"
        },
        {
            "text": "Deer sighting near Estes Park visitor center",
            "keyword": "deer"
        },
        {
            "text": "Mountain lion tracks found on Mount Evans summit trail at 14,000 feet",
            "keyword": "mountain lion"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n=== Test Case {i} ===")
        logger.info(f"Text: {test['text']}")
        
        is_valid, confidence, location_data = validator.validate_sighting_with_llm(test['text'], test['keyword'], test['keyword'])
        
        logger.info(f"Valid: {is_valid}")
        logger.info(f"Confidence: {confidence}")
        logger.info(f"Location data: {json.dumps(location_data, indent=2)}")
        
        if location_data.get('coordinates'):
            logger.success(f"✓ Coordinates extracted: {location_data['coordinates']}")
        else:
            logger.warning("✗ No coordinates extracted")

if __name__ == "__main__":
    test_location_extraction()