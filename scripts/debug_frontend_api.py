#!/usr/bin/env python3
"""
Debug why frontend isn't showing map markers.
"""

import requests
import json
from loguru import logger

def test_api_endpoints():
    """Test both API endpoints to see what data is available."""
    
    # Test the regular sightings endpoint with 5-day filter
    logger.info("Testing regular sightings endpoint with 5-day filter...")
    try:
        response = requests.get("http://localhost:8002/api/v1/sightings", params={
            "start_date": "2025-06-24",
            "limit": 100
        })
        data = response.json()
        
        logger.info(f"Total sightings: {data.get('total', 0)}")
        logger.info(f"Returned sightings: {len(data.get('sightings', []))}")
        
        # Check how many have location data
        with_location = 0
        for s in data.get('sightings', []):
            if s.get('location') or (s.get('lat') and s.get('lng')):
                with_location += 1
                if with_location <= 3:
                    logger.info(f"  {s['species']} - location: {s.get('location', 'coordinates in lat/lng')}")
        
        logger.info(f"Sightings with location data: {with_location}")
        
    except Exception as e:
        logger.error(f"Failed to fetch regular sightings: {e}")
    
    # Test the coordinate-specific endpoint
    logger.info("\nTesting coordinate-specific endpoint...")
    try:
        response = requests.get("http://localhost:8002/api/v1/sightings/with-coords")
        data = response.json()
        
        logger.info(f"Total with coordinates: {data.get('total', 0)}")
        logger.info(f"First 3 sightings:")
        
        for s in data.get('sightings', [])[:3]:
            logger.info(f"  {s['species']} at {s.get('location_name', 'Unknown')} - {s['location']}")
            
    except Exception as e:
        logger.error(f"Failed to fetch coordinate sightings: {e}")
    
    # Test if frontend is actually calling the API
    logger.info("\nChecking if frontend can reach API...")
    try:
        # Test CORS
        response = requests.get("http://localhost:8002/api/v1/health", 
                              headers={"Origin": "http://localhost:5173"})
        logger.info(f"Health check: {response.json()}")
    except Exception as e:
        logger.error(f"Health check failed: {e}")

if __name__ == "__main__":
    test_api_endpoints()