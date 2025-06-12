#!/usr/bin/env python3
"""
Test script for SummitPost scraper.
"""

import sys
import os
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.summitpost_scraper import SummitPostScraper

def test_summitpost_scraper():
 """Test the SummitPost scraper functionality."""
 print("\n" + "="*60)
 print("TESTING SUMMITPOST SCRAPER")
 print("="*60)

 try:
 # Initialize scraper
 scraper = SummitPostScraper()
 print(" SummitPost scraper initialized")
 print(f" - Rate limit: {scraper.rate_limit} seconds")
 print(f" - Source: {scraper.source_name}")

 # Test scraping
 print("\n Scraping SummitPost content...")
 sightings = scraper.scrape(lookback_days=7)

 print(f"\n Found {len(sightings)} wildlife sightings")

 # Show results by peak
 peaks = {}
 for sighting in sightings:
 peak = sighting.get('trail_name', 'Unknown')
 if peak not in peaks:
 peaks[peak] = []
 peaks[peak].append(sighting)

 print("\n Sightings by Peak:")
 for peak, peak_sightings in peaks.items():
 print(f"\n {peak} ({len(peak_sightings)} sightings):")
 for s in peak_sightings:
 species = s.get('species', 'unknown')
 keyword = s.get('keyword_matched', '')
 context = s.get('raw_text', '')[:80] + '...'
 print(f" - {species} ('{keyword}'): {context}")

 # Test keyword matching
 print("\n Species Summary:")
 species_count = {}
 for s in sightings:
 species = s.get('species', 'unknown')
 species_count[species] = species_count.get(species, 0) + 1

 for species, count in species_count.items():
 print(f" - {species}: {count} mentions")

 # Check data structure
 if sightings:
 print("\n Sample Sighting Structure:")
 sample = sightings[0]
 for key, value in sample.items():
 if key != 'raw_text': # Skip long text
 print(f" - {key}: {value}")

 return True

 except Exception as e:
 print(f" Error: {e}")
 logger.error(f"SummitPost test failed: {e}")
 return False

def main():
 """Run the test."""
 success = test_summitpost_scraper()

 if success:
 print("\n SummitPost scraper test PASSED!")
 else:
 print("\n SummitPost scraper test FAILED!")

if __name__ == "__main__":
 main()
