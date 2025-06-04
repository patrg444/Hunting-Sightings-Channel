#!/usr/bin/env python3
"""
Diagnose what HTML we get from 14ers.com trip reports page
"""

import requests
from bs4 import BeautifulSoup

def diagnose_trips():
    """Check what's on the actual trip reports page."""
    url = "https://www.14ers.com/php14ers/tripmain.php"
    
    print(f"Fetching {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save the HTML
            with open('14ers_trips.html', 'w') as f:
                f.write(response.text)
            print("Saved HTML to 14ers_trips.html")
            
            # Check for forms (might need to submit a form to see reports)
            forms = soup.find_all('form')
            print(f"\nFound {len(forms)} forms")
            
            # Check for any error messages
            error_divs = soup.find_all(text=lambda t: t and ('error' in t.lower() or 'login' in t.lower()))
            if error_divs:
                print("\nPossible login/error messages found:")
                for err in error_divs[:3]:
                    print(f"  - {err.strip()[:100]}")
            
            # Look for any links with 'trip' in href
            trip_links = soup.find_all('a', href=lambda x: x and 'trip' in x.lower() if x else False)
            print(f"\nFound {len(trip_links)} links with 'trip' in href")
            for link in trip_links[:5]:
                print(f"  - {link.get('href')} | {link.get_text(strip=True)[:50]}")
            
            # Check if page requires login
            login_indicators = ['log in', 'login', 'sign in', 'password', 'username']
            page_text = soup.get_text().lower()
            for indicator in login_indicators:
                if indicator in page_text:
                    print(f"\n⚠️  Page might require login - found '{indicator}' in text")
                    break
                    
        else:
            print(f"Failed to fetch page: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_trips()
