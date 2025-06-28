#!/usr/bin/env python3
"""
Test the LLM validator with the updated GPT-4.1 nano model.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.llm_validator import LLMValidator
from loguru import logger

def test_validator():
    """Test the LLM validator with sample wildlife texts."""
    
    validator = LLMValidator()
    
    # Test texts
    test_cases = [
        {
            "text": "Saw a huge bull elk this morning near the bridge on Maroon Creek trail. Must have been at least 6x6!",
            "keyword": "elk",
            "source": "Reddit - ColoradoHunting"
        },
        {
            "text": "Beautiful hike today at Georgetown Lake. Spotted some bighorn sheep on the cliffs above the lake.",
            "keyword": "bighorn",
            "source": "Google Maps Review"
        },
        {
            "text": "Great fishing at the lake but no wildlife today.",
            "keyword": "deer",
            "source": "Google Maps Review"
        }
    ]
    
    logger.info("Testing LLM validator with GPT-4.1 nano model...")
    
    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n--- Test Case {i} ---")
        logger.info(f"Text: {test['text'][:100]}...")
        logger.info(f"Keyword: {test['keyword']}")
        logger.info(f"Source: {test['source']}")
        
        try:
            # Test the full analysis method
            result = validator.analyze_full_text_for_sighting(
                test['text'],
                test['keyword'],
                test['source']
            )
            
            if result:
                logger.success("✓ Wildlife sighting detected!")
                logger.info(f"  Species: {result.get('species', 'Unknown')}")
                logger.info(f"  Location: {result.get('location_name', 'Unknown')}")
                logger.info(f"  Confidence Radius: {result.get('location_confidence_radius', 'Unknown')} miles")
                logger.info(f"  Confidence: {result.get('confidence', 'Unknown')}%")
            else:
                logger.info("✗ No wildlife sighting detected")
                
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    test_validator()