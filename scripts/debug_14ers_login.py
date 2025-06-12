#!/usr/bin/env python3
"""
Debug 14ers.com login process
"""

import requests
from bs4 import BeautifulSoup

def debug_login():
 """Debug the login process for 14ers.com."""

 session = requests.Session()
 session.headers.update({
 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
 })

 login_url = "https://www.14ers.com/php14ers/loginviaforum.php"

 print(f"Step 1: Fetching login page from {login_url}")
 response = session.get(login_url)
 print(f"Status: {response.status_code}")

 if response.status_code == 200:
 soup = BeautifulSoup(response.text, 'html.parser')

 # Look for form
 forms = soup.find_all('form')
 print(f"\nFound {len(forms)} forms")

 for i, form in enumerate(forms):
 print(f"\nForm {i}:")
 action = form.get('action', 'No action')
 method = form.get('method', 'No method')
 print(f" Action: {action}")
 print(f" Method: {method}")

 # Find all input fields
 inputs = form.find_all('input')
 print(f" Input fields:")
 for inp in inputs:
 name = inp.get('name', 'unnamed')
 type_ = inp.get('type', 'text')
 value = inp.get('value', '')
 print(f" - {name} (type: {type_}, value: {value[:20] if value else 'empty'})")

 # Save login page for inspection
 with open('14ers_login_page.html', 'w') as f:
 f.write(response.text)
 print("\nSaved login page to 14ers_login_page.html")

 # Try login with different field variations
 print("\nStep 2: Attempting login...")

 # Common login field names
 login_attempts = [
 {
 'username': 'nicholasreichert86',
 'password': 'Huntingsightingchannel86',
 'autologin': 'on',
 'login': 'Login'
 },
 {
 'user': 'nicholasreichert86',
 'pass': 'Huntingsightingchannel86',
 'submit': 'Login'
 },
 {
 'vb_login_username': 'nicholasreichert86',
 'vb_login_password': 'Huntingsightingchannel86',
 'do': 'login'
 }
 ]

 for i, data in enumerate(login_attempts):
 print(f"\nAttempt {i+1} with fields: {list(data.keys())}")
 response = session.post(login_url, data=data)
 print(f"Response status: {response.status_code}")

 # Check for success indicators
 if 'logout' in response.text.lower():
 print(" Found 'logout' in response - login might be successful!")
 break
 elif response.status_code == 302:
 print(" Got redirect - login might be successful!")
 print(f"Redirect to: {response.headers.get('Location', 'Unknown')}")
 break
 else:
 print(" No success indicators found")

 else:
 print(f"Failed to fetch login page: {response.status_code}")

if __name__ == "__main__":
 debug_login()
