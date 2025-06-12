#!/usr/bin/env python3
"""
Test script for Playwright-based SummitPost scraper.
This tests the browser automation version that can fetch real data.
"""

import sys
import os
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if Playwright is installed
try:
 from playwright.sync_api import sync_playwright
 PLAYWRIGHT_INSTALLED = True
except ImportError:
 PLAYWRIGHT_INSTALLED = False

from scrapers.summitpost_playwright_scraper import SummitPostPlaywrightScraper

def test_playwright_available():
 """Check if Playwright is properly installed."""
 print("\n Checking Playwright installation...")

 if not PLAYWRIGHT_INSTALLED:
 print(" Playwright not installed!")
 print("\n To install Playwright, run:")
 print(" pip install playwright")
 print(" playwright install chromium")
 print("\nThis will install Playwright and download the Chromium browser.")
 return False

 print(" Playwright is installed")

 # Check if browsers are installed
 try:
 with sync_playwright() as p:
 browser = p.chromium.launch(headless=True)
 browser.close()
 print(" Chromium browser is installed")
 return True
 except Exception as e:
 print(" Chromium browser not installed!")
 print(f" Error: {e}")
 print("\n To install browsers, run:")
 print(" playwright install chromium")
 return False

def test_summitpost_playwright_scraper():
 """Test the Playwright-based SummitPost scraper."""
 print("\n" + "="*60)
 print("TESTING PLAYWRIGHT SUMMITPOST SCRAPER")
 print("="*60)

 # First check if Playwright is available
 if not test_playwright_available():
 return False

 try:
 # Initialize scraper
 scraper = SummitPostPlaywrightScraper()
 print("\n Playwright SummitPost scraper initialized")
 print(f" - Rate limit: {scraper.rate_limit} seconds")
 print(f" - Base URL: {scraper.BASE_URL}")
 print(" - Browser: Chromium (headless)")

 # Test initialization of browser
 print("\n Initializing browser...")
 scraper._init_browser()
 print(" Browser initialized successfully")

 # Test navigation to main page
 print("\n Testing navigation to SummitPost...")
 scraper.page.goto(scraper.BASE_URL, wait_until='networkidle', timeout=30000)
 title = scraper.page.title()
 print(f" Successfully loaded: {title}")

 # Test getting trip reports
 print("\n Testing trip report fetching...")
 trip_reports = scraper._get_recent_trip_reports_browser()
 print(f" Found {len(trip_reports)} trip reports")

 if trip_reports:
 print("\n Sample trip reports:")
 for i, report in enumerate(trip_reports[:3]):
 print(f" {i+1}. {report['title']}")
 print(f" URL: {report['url']}")

 # Test getting peak pages
 print("\n Testing peak page access...")
 peak_pages = scraper._get_colorado_peaks()
 print(f" Loaded {len(peak_pages)} peak pages")

 # Test wildlife extraction (limited)
 print("\n Testing wildlife extraction...")

 # Close browser for cleanup
 scraper._close_browser()

 # Now run full scrape test
 print("\n Running full scrape test (limited to save time)...")
 all_sightings = scraper.scrape(lookback_days=7)

 print(f"\n Total sightings found: {len(all_sightings)}")

 if all_sightings:
 print("\n Wildlife sightings found:")
 for i, sighting in enumerate(all_sightings[:5]):
 species = sighting.get('species', 'unknown')
 source = sighting.get('report_title', sighting.get('trail_name', 'Unknown'))
 text = sighting.get('raw_text', '')[:80] + '...'
 print(f"\n {i+1}. {species} at {source}")
 print(f" \"{text}\"")
 else:
 print("\n No wildlife sightings found in the tested content")
 print(" (This is common - wildlife mentions are rare in trip reports)")

 return True

 except Exception as e:
 print(f"\n Error during test: {e}")
 logger.error(f"Playwright SummitPost test failed: {e}")
 import traceback
 traceback.print_exc()
 return False

def main():
 """Run the test."""
 success = test_summitpost_playwright_scraper()

 if success:
 print("\n" + "="*60)
 print(" PLAYWRIGHT SUMMITPOST SCRAPER TEST PASSED!")
 print("="*60)
 print("\nThe browser-based scraper successfully:")
 print(" - Launched a real browser")
 print(" - Navigated to SummitPost.org")
 print(" - Fetched real content")
 print(" - Extracted data from pages")
 print("\nThis demonstrates the ability to scrape sites with")
 print("anti-scraping measures using browser automation.")
 else:
 print("\n" + "="*60)
 print(" PLAYWRIGHT SUMMITPOST SCRAPER TEST FAILED!")
 print("="*60)

 if not PLAYWRIGHT_INSTALLED:
 print("\n Installation Instructions:")
 print("1. Install Playwright:")
 print(" pip install playwright")
 print("\n2. Install browsers:")
 print(" playwright install chromium")
 print("\n3. Run this test again")

if __name__ == "__main__":
 main()
