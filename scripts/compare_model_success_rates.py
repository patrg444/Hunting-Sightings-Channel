#!/usr/bin/env python3
"""
Compare success rates between GPT-4.1 nano and GPT-4o mini models for coordinate extraction.
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Test dataset of Colorado locations with known coordinates
TEST_LOCATIONS = [
    {"name": "Bear Lake, RMNP", "expected": [40.3845, -105.6824]},
    {"name": "Estes Park", "expected": [40.3775, -105.5253]},
    {"name": "Mount Evans", "expected": [39.5883, -105.6438]},
    {"name": "Maroon Bells", "expected": [39.0708, -106.9890]},
    {"name": "Quandary Peak", "expected": [39.3995, -106.1005]},
    {"name": "Trail Ridge Road", "expected": [40.3925, -105.6836]},
    {"name": "Grand Lake", "expected": [40.252, -105.8233]},
    {"name": "Durango", "expected": [37.2753, -107.8801]},
    {"name": "Aspen", "expected": [39.1911, -106.8175]},
    {"name": "Vail", "expected": [39.6403, -106.3742]},
    {"name": "Rocky Mountain National Park", "expected": [40.3428, -105.6836]},
    {"name": "Staunton State Park", "expected": [39.406, -105.2875]},
    {"name": "Bear Creek Falls, Ouray", "expected": [38.0225, -107.67]},
    {"name": "Crestone, Sangre de Cristo Wilderness Area", "expected": [37.9989, -105.6989]},
    {"name": "Glacier Gorge Trailhead, RMNP", "expected": [40.3725, -105.634]},
    {"name": "Deer Mountain Trailhead near Estes Park", "expected": [40.3665, -105.525]},
    {"name": "Yellow Jacket Mine, Bear Creek", "expected": None},  # Vague location
    {"name": "Unnamed peak, Bear Creek, Ouray", "expected": None},  # Vague location
    {"name": "somewhere in the mountains", "expected": None},  # Very vague
    {"name": "near a lake", "expected": None}  # Too vague
]

def test_model(model_name: str, test_locations: List[Dict]) -> Dict:
    """Test a model with the given locations and return results."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing model: {model_name}")
    logger.info(f"{'='*60}")
    
    results = {
        "model": model_name,
        "total_tests": len(test_locations),
        "successful_extractions": 0,
        "failed_extractions": 0,
        "correct_coordinates": 0,
        "incorrect_coordinates": 0,
        "null_when_expected": 0,
        "coordinates_when_null_expected": 0,
        "details": []
    }
    
    # Build batch prompt
    prompt = """You are a Colorado geography expert. Extract precise coordinates for these wildlife sighting locations.

Locations to geocode:
"""
    
    for i, loc in enumerate(test_locations):
        prompt += f"\n{i+1}. Wildlife at {loc['name']}"
    
    prompt += """

Return a JSON array with coordinates:
[
  {"index": 1, "coordinates": [lat, lon] or null},
  {"index": 2, "coordinates": [lat, lon] or null},
  ...
]

Use these known Colorado coordinates:
- Bear Lake RMNP: [40.3845, -105.6824]
- Estes Park: [40.3775, -105.5253]
- Mount Evans: [39.5883, -105.6438]
- Maroon Bells: [39.0708, -106.9890]
- Quandary Peak: [39.3995, -106.1005]
- Trail Ridge Road: [40.3925, -105.6836]
- Grand Lake: [40.252, -105.8233]
- Durango: [37.2753, -107.8801]
- Aspen: [39.1911, -106.8175]
- Vail: [39.6403, -106.3742]

Provide coordinates for any recognizable Colorado location. Use null only if impossible to determine."""

    try:
        start_time = time.time()
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a precise geographic coordinate expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,  # Increased for nano model
            temperature=0.1
        )
        elapsed = time.time() - start_time
        
        result_text = response.choices[0].message.content.strip()
        
        # Log raw response for debugging
        logger.info(f"Raw response from {model_name} (first 300 chars): {result_text[:300]}...")
        
        # Save full response for nano model debugging
        if "nano" in model_name:
            with open(f"nano_response_{model_name.replace('.', '_')}.txt", "w") as f:
                f.write(result_text)
            logger.info(f"Saved full nano response to nano_response_{model_name.replace('.', '_')}.txt")
        
        # Extract JSON
        if "```json" in result_text:
            start = result_text.find("```json") + 7
            end = result_text.find("```", start)
            result_text = result_text[start:end].strip()
        elif "```" in result_text:
            start = result_text.find("```") + 3
            end = result_text.find("```", start)
            result_text = result_text[start:end].strip()
        
        # Try to find JSON array in the response
        if not result_text.startswith('['):
            # Look for array pattern in the text
            import re
            json_match = re.search(r'\[[\s\S]*\]', result_text)
            if json_match:
                result_text = json_match.group(0)
        
        # Remove comments from JSON (nano model adds them)
        import re
        result_text = re.sub(r'//.*$', '', result_text, flags=re.MULTILINE)
        
        # Parse results
        extracted_data = json.loads(result_text)
        
        # Analyze results
        for item in extracted_data:
            idx = item['index'] - 1
            if 0 <= idx < len(test_locations):
                test_loc = test_locations[idx]
                extracted_coords = item.get('coordinates')
                expected_coords = test_loc['expected']
                
                detail = {
                    "location": test_loc['name'],
                    "extracted": extracted_coords,
                    "expected": expected_coords,
                    "status": ""
                }
                
                if extracted_coords and isinstance(extracted_coords, list) and len(extracted_coords) == 2:
                    lat, lng = extracted_coords
                    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                        results["successful_extractions"] += 1
                        
                        if expected_coords:
                            # Check accuracy (within 0.01 degrees)
                            if abs(lat - expected_coords[0]) < 0.01 and abs(lng - expected_coords[1]) < 0.01:
                                results["correct_coordinates"] += 1
                                detail["status"] = "✓ Correct"
                            else:
                                results["incorrect_coordinates"] += 1
                                detail["status"] = f"✗ Incorrect (off by {abs(lat - expected_coords[0]):.4f}, {abs(lng - expected_coords[1]):.4f})"
                        else:
                            # Expected null but got coordinates
                            results["coordinates_when_null_expected"] += 1
                            detail["status"] = "⚠ Coords when null expected"
                    else:
                        results["failed_extractions"] += 1
                        detail["status"] = "✗ Invalid coordinate format"
                else:
                    results["failed_extractions"] += 1
                    if expected_coords is None:
                        results["null_when_expected"] += 1
                        detail["status"] = "✓ Correctly null"
                    else:
                        detail["status"] = "✗ Failed to extract"
                
                results["details"].append(detail)
        
        results["response_time"] = elapsed
        logger.info(f"Response time: {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"Error testing {model_name}: {e}")
        results["error"] = str(e)
    
    return results

def calculate_success_rate(results: Dict) -> float:
    """Calculate overall success rate."""
    correct_extractions = results["correct_coordinates"] + results["null_when_expected"]
    total_with_known_answer = results["total_tests"] - results["coordinates_when_null_expected"]
    
    if total_with_known_answer > 0:
        return (correct_extractions / total_with_known_answer) * 100
    return 0

def main():
    """Run comparison tests."""
    logger.info("Starting model comparison for coordinate extraction...")
    
    # Test both models
    models = ["gpt-4o-mini", "gpt-4.1-nano-2025-04-14"]
    all_results = []
    
    for model in models:
        results = test_model(model, TEST_LOCATIONS)
        all_results.append(results)
        
        # Calculate success rate
        success_rate = calculate_success_rate(results)
        results["success_rate"] = success_rate
        
        # Print summary
        logger.info(f"\n{model} Summary:")
        logger.info(f"  Total tests: {results['total_tests']}")
        logger.info(f"  Successful extractions: {results['successful_extractions']}")
        logger.info(f"  Failed extractions: {results['failed_extractions']}")
        logger.info(f"  Correct coordinates: {results['correct_coordinates']}")
        logger.info(f"  Incorrect coordinates: {results['incorrect_coordinates']}")
        logger.info(f"  Correctly null: {results['null_when_expected']}")
        logger.info(f"  Overall success rate: {success_rate:.1f}%")
        
        if "response_time" in results:
            logger.info(f"  Response time: {results['response_time']:.2f}s")
        
        # Add delay between models
        if model != models[-1]:
            time.sleep(2)
    
    # Compare results
    logger.info(f"\n{'='*60}")
    logger.info("COMPARISON SUMMARY")
    logger.info(f"{'='*60}")
    
    for result in all_results:
        logger.info(f"{result['model']}:")
        logger.info(f"  Success rate: {result['success_rate']:.1f}%")
        response_time = result.get('response_time', 'N/A')
        if response_time != 'N/A':
            logger.info(f"  Response time: {response_time:.2f}s")
        else:
            logger.info(f"  Response time: {response_time}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"model_comparison_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "test_locations": TEST_LOCATIONS,
            "results": all_results
        }, f, indent=2)
    
    logger.info(f"\nDetailed results saved to: {output_file}")
    
    # Print sample comparisons
    logger.info("\nSample location comparisons:")
    for i in range(min(5, len(TEST_LOCATIONS))):
        loc = TEST_LOCATIONS[i]
        logger.info(f"\n{loc['name']}:")
        for result in all_results:
            if i < len(result["details"]):
                detail = result["details"][i]
                logger.info(f"  {result['model']}: {detail['extracted']} - {detail['status']}")

if __name__ == "__main__":
    main()