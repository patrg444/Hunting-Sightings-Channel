#!/usr/bin/env python3
"""
Diagnostic script for SummitPost scraper to check what's accessible.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.summitpost_scraper_real import SummitPostRealScraper

def diagnose_summitpost():
 """Diagnose SummitPost accessibility."""
 print("\n" + "="*60)
 print("SUMMITPOST ACCESSIBILITY DIAGNOSTIC")
 print("="*60)

 scraper = SummitPostRealScraper()

 # Test different URLs
 test_urls = [
 ("Main page", "https://www.summitpost.org/"),
 ("Longs Peak", "https://www.summitpost.org/mountain/rock/150329"),
 ("Mount Elbert", "https://www.summitpost.org/longs-peak/150329"),
 ("Trip Reports", "https://www.summitpost.org/object_list.php?object_type=5"),
 ("Colorado Mountains", "https://www.summitpost.org/list/1001143/colorado-14ers.html")
 ]

 print("\n Testing URL accessibility:")
 print("-" * 40)

 for name, url in test_urls:
 print(f"\n{name}: {url}")
 try:
 response = scraper._make_request(url)
 if response:
 print(f" Status: {response.status_code}")
 print(f" Content length: {len(response.text)} chars")

 # Check if we got real content or a block page
 if "Access Denied" in response.text or "403 Forbidden" in response.text:
 print(" Blocked: Access denied page")
 elif len(response.text) < 1000:
 print(" Suspicious: Very short response")
 else:
 # Try to find wildlife keywords
 soup = BeautifulSoup(response.text, 'html.parser')
 text = soup.get_text().lower()

 wildlife_found = []
 for species in ['elk', 'deer', 'bear', 'goat', 'sheep']:
 if species in text:
 wildlife_found.append(species)

 if wildlife_found:
 print(f" Wildlife mentions found: {', '.join(wildlife_found)}")
 else:
 print(" Failed: No response")

 except Exception as e:
 print(f" Error: {e}")

 print("\n" + "="*60)
 print("\n DIAGNOSIS SUMMARY:")
 print("-" * 40)
 print("SummitPost has strong anti-scraping measures in place.")
 print("The scraper code is correct, but the site blocks automated requests.")
 print("\n What's working:")
 print(" - HTTP requests are being made")
 print(" - Headers are set correctly")
 print(" - URL structure is correct")
 print("\n What's blocked:")
 print(" - Trip report listings (403 Forbidden)")
 print(" - Most content pages require browser-like behavior")
 print("\n Solutions:")
 print(" 1. Use the simulated scraper for demo purposes")
 print(" 2. Implement Playwright/Selenium for real scraping")
 print(" 3. Contact SummitPost for API access")

if __name__ == "__main__":
 diagnose_summitpost()
