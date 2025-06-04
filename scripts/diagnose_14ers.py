#!/usr/bin/env python3
"""
Diagnose 14ers.com HTML structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup

def diagnose_14ers():
    """Check what's actually on the 14ers.com trip reports page."""
    url = "https://www.14ers.com/tripreports.php"
    
    print(f"Fetching {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Hunting Sightings Bot 1.0; Contact: patrg444@gmail.com)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for tables
            tables = soup.find_all('table')
            print(f"\nFound {len(tables)} tables on the page")
            
            # Check for table classes
            for i, table in enumerate(tables):
                classes = table.get('class', [])
                print(f"Table {i}: classes = {classes}")
                
                # Show first row
                first_row = table.find('tr')
                if first_row:
                    cells = first_row.find_all(['td', 'th'])
                    print(f"  First row: {[cell.get_text(strip=True)[:20] for cell in cells]}")
            
            # Look for other potential containers
            print("\n\nLooking for divs with 'report' in class name:")
            report_divs = soup.find_all('div', class_=lambda x: x and 'report' in x.lower() if isinstance(x, str) else False)
            print(f"Found {len(report_divs)} divs with 'report' in class")
            
            # Show page title
            title = soup.find('title')
            if title:
                print(f"\nPage title: {title.get_text()}")
                
            # Save HTML for inspection
            with open('14ers_page.html', 'w') as f:
                f.write(response.text)
            print("\nSaved full HTML to 14ers_page.html for inspection")
            
        else:
            print(f"Failed to fetch page: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_14ers()
