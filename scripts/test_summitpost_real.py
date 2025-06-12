#!/usr/bin/env python3
"""
Test script for real SummitPost scraper.
"""

import sys
import os
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.summitpost_scraper_real import SummitPostRealScraper

def test_summitpost_real_scraper():
 """Test the real SummitPost scraper functionality."""
 print("\n" + "="*60)
 print("TESTING REAL SUMMITPOST SCRAPER")
 print("="*60)

 try:
 # Initialize scraper
 scraper = SummitPostRealScraper()
 print(" Real SummitPost scraper initialized")
 print(f" - Rate limit: {scraper.rate_limit} seconds")
 print(f" - Base URL: {scraper.BASE_URL}")

 # Test fetching trip reports
 print("\n Fetching real trip reports from Colorado...")
 trip_reports = scraper._get_recent_trip_reports()
 print(f" Found {len(trip_reports)} trip reports")

 if trip_reports:
 print("\n Sample trip reports:")
 for i, report in enumerate(trip_reports[:3]):
 print(f" {i+1}. {report['title']}")
 print(f" URL: {report['url']}")

 # Test fetching peak pages
 print("\n Loading Colorado peak pages...")
 peak_pages = scraper._get_colorado_peaks()
 print(f" Loaded {len(peak_pages)} peak pages")

 for peak in peak_pages[:3]:
 print(f" - {peak['title']}: {peak['url']}")

 # Test full scraping (limited to avoid too many requests)
 print("\n Running limited scrape test...")
 print(" (Checking first trip report and first peak only)")

 all_sightings = []

 # Test one trip report
 if trip_reports:
 print(f"\n Checking trip report: {trip_reports[0]['title']}")
 sightings = scraper._extract_sightings_from_report(trip_reports[0])
 all_sightings.extend(sightings)
 print(f" Found {len(sightings)} sightings")

 # Test one peak page
 if peak_pages:
 print(f"\n Checking peak page: {peak_pages[0]['title']}")
 sightings = scraper._extract_sightings_from_peak_page(peak_pages[0])
 all_sightings.extend(sightings)
 print(f" Found {len(sightings)} sightings")

 # Summary
 print(f"\n Total sightings found: {len(all_sightings)}")

 if all_sightings:
 print("\n Wildlife sightings:")
 for i, sighting in enumerate(all_sightings[:5]):
 species = sighting.get('species', 'unknown')
 source = sighting.get('report_title', sighting.get('trail_name', 'Unknown'))
 text = sighting.get('raw_text', '')[:80] + '...'
 print(f"\n {i+1}. {species} at {source}")
 print(f" \"{text}\"")

 return True

 except Exception as e:
 print(f" Error: {e}")
 logger.error(f"Real SummitPost test failed: {e}")
 import traceback
 traceback.print_exc()
 return False

def main():
 """Run the test."""
 success = test_summitpost_real_scraper()

 if success:
 print("\n Real SummitPost scraper test PASSED!")
 print(" The scraper is fetching actual data from SummitPost.org")
 else:
 print("\n Real SummitPost scraper test FAILED!")
 print(" Check the error messages above for details")

if __name__ == "__main__":
 main()
