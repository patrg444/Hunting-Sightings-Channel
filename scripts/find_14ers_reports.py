#!/usr/bin/env python3
"""
Find where trip reports are on 14ers.com
"""

import requests
from bs4 import BeautifulSoup

def find_trip_reports():
    """Try to find trip reports on 14ers.com."""
    
    # Try different possible URLs
    urls_to_try = [
        "https://www.14ers.com",
        "https://www.14ers.com/routes.php",
        "https://www.14ers.com/reports",
        "https://www.14ers.com/trip-reports"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in urls_to_try:
        print(f"\nTrying {url}...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for links with "report" in them
                report_links = soup.find_all('a', href=lambda x: x and 'report' in x.lower() if x else False)
                if report_links:
                    print(f"Found {len(report_links)} links with 'report':")
                    for link in report_links[:5]:
                        print(f"  - {link.get('href')} | {link.get_text(strip=True)[:50]}")
                
                # Look for links to specific peaks
                peak_links = soup.find_all('a', href=lambda x: x and '/route.php' in x if x else False)
                if peak_links:
                    print(f"\nFound {len(peak_links)} route links")
                    for link in peak_links[:3]:
                        print(f"  - {link.get('href')} | {link.get_text(strip=True)[:50]}")
                        
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n\nNote: Many sites now use JavaScript to load content dynamically.")
    print("The actual trip reports might be loaded via AJAX after page load.")

if __name__ == "__main__":
    find_trip_reports()
