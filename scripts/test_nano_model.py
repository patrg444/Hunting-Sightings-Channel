#!/usr/bin/env python3
"""
Test GPT-4.1 nano model specifically.
"""
import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def test_nano_simple():
    """Test nano with a simple prompt."""
    
    prompt = """Extract coordinates for these Colorado locations:
1. Bear Lake, RMNP
2. Estes Park
3. Mount Evans

Return JSON array: [{"index": 1, "coordinates": [lat, lon]}, ...]"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"Raw response:\n{result}")
        
        # Try parsing
        try:
            data = json.loads(result)
            logger.success(f"Successfully parsed JSON: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.info(f"Response length: {len(result)} chars")
            
            # Try to find where the error is
            try:
                # Parse line by line
                lines = result.split('\n')
                for i, line in enumerate(lines):
                    logger.info(f"Line {i+1}: {repr(line)}")
            except:
                pass
        
    except Exception as e:
        logger.error(f"API error: {e}")

if __name__ == "__main__":
    test_nano_simple()