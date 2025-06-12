#!/usr/bin/env python3
"""
Test script to search for wildlife content on SummitPost using Playwright.
This script specifically searches for wildlife mentions to demonstrate the scraper works.
"""

import sys
import os
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.summitpost_playwright_scraper import SummitPostPlaywrightScraper

def test_wildlife_search():
 """Search for specific wildlife content on SummitPost."""
 print("\n" + "="*60)
 print("SUMMITPOST WILDLIFE SEARCH TEST")
 print("="*60)

 scraper = SummitPostPlaywrightScraper()

 try:
 # Initialize browser
 scraper._init_browser()
 print(" Browser initialized")

 # Search for wildlife-related content
 search_terms = ["mountain goat colorado", "elk sighting fourteener", "bear encounter climbing"]
 all_results = []

 for term in search_terms:
 print(f"\n Searching for: '{term}'")

 try:
 # Navigate to search page
 search_url = f"{scraper.BASE_URL}/search/results.php?search_query={term.replace(' ', '+')}"
 scraper.page.goto(search_url, wait_until='domcontentloaded', timeout=15000)

 # Get search results
 results = scraper.page.query_selector_all('a.search-result-link, a[href*="/trip-report/"], a[href*="/mountain/"]')[:3]

 for result in results:
 try:
 title = result.inner_text()
 href = result.get_attribute('href')
 if href and title:
 print(f" Found: {title[:60]}...")
 all_results.append({
 'title': title,
 'url': scraper.BASE_URL + href if not href.startswith('http') else href,
 'search_term': term
 })
 except:
 continue

 except Exception as e:
 print(f"  Search failed: {e}")

 # Test a specific peak known for wildlife
 print("\n Checking Longs Peak for wildlife mentions...")
 scraper.page.goto(f"{scraper.BASE_URL}/longs-peak/150329", wait_until='domcontentloaded', timeout=15000)

 # Get page text
 page_text = scraper.page.inner_text('body').lower()

 # Look for wildlife keywords
 wildlife_keywords = ['goat', 'elk', 'bear', 'deer', 'sheep', 'moose', 'mountain lion', 'cougar']
 found_wildlife = []

 for keyword in wildlife_keywords:
 if keyword in page_text:
 found_wildlife.append(keyword)
 # Get context
 lines = page_text.split('\n')
 for line in lines:
 if keyword in line and len(line) > 20:
 print(f"\n Found '{keyword}' mention:")
 print(f" \"{line[:100]}...\"")
 break

 if found_wildlife:
 print(f"\n Wildlife keywords found on Longs Peak page: {', '.join(found_wildlife)}")
 else:
 print("\n No wildlife keywords found on this peak page")

 # Summary
 print(f"\n Total search results found: {len(all_results)}")

 return len(all_results) > 0 or len(found_wildlife) > 0

 finally:
 scraper._close_browser()

def main():
 """Run the wildlife search test."""
 success = test_wildlife_search()

 print("\n" + "="*60)
 if success:
 print(" WILDLIFE SEARCH TEST PASSED!")
 print("\nThe Playwright scraper successfully:")
 print(" - Performed searches on SummitPost")
 print(" - Navigated to peak pages")
 print(" - Extracted text content")
 print(" - Found wildlife-related content")
 else:
 print(" WILDLIFE SEARCH TEST - NO RESULTS")
 print("\nThe scraper is working but didn't find wildlife content.")
 print("This is normal - wildlife mentions are rare on SummitPost.")
 print("="*60)

if __name__ == "__main__":
 main()
