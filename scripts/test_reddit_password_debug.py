#!/usr/bin/env python3
"""
Debug Reddit password authentication issues.
"""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_password_auth_debug():
 """Debug Reddit password authentication."""
 CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
 CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
 USERNAME = "Fit-Indication-2067"
 PASSWORD = "huntingsightingchannel"
 USER_AGENT = "script:HuntingSightingsBot:1.0 (by /u/Fit-Indication-2067)"

 print("=== Reddit Password Authentication Debug ===")
 print(f"Client ID: {CLIENT_ID}")
 print(f"Client Secret: {CLIENT_SECRET}")
 print(f"Username: {USERNAME}")
 print(f"Password: {'*' * len(PASSWORD)}")
 print(f"User Agent: {USER_AGENT}")

 # Test different scenarios
 print("\n--- Test 1: Standard password auth ---")
 auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
 data = {
 "grant_type": "password",
 "username": USERNAME,
 "password": PASSWORD
 }
 headers = {"User-Agent": USER_AGENT}

 resp = requests.post(
 "https://www.reddit.com/api/v1/access_token",
 auth=auth,
 data=data,
 headers=headers
 )

 print(f"Status: {resp.status_code}")
 print(f"Headers: {dict(resp.headers)}")
 print(f"Response: {resp.text}")

 # Parse response
 try:
 json_resp = resp.json()
 if 'error' in json_resp:
 print(f"\nError type: {json_resp.get('error')}")
 print(f"Error description: {json_resp.get('error_description', 'N/A')}")

 # Common error interpretations
 if json_resp.get('error') == 'invalid_grant':
 print("\nPossible causes:")
 print("- Incorrect username or password")
 print("- Account has 2FA enabled (not supported with password grant)")
 print("- Account was created with Google/Apple login and password wasn't properly set")
 elif json_resp.get('error') == 'unauthorized_client':
 print("\nThe app is not authorized for password grant")
 print("This usually means the app type doesn't support this auth method")
 except:
 pass

 # Test with different username format
 print("\n--- Test 2: Without 'u/' prefix ---")
 data2 = {
 "grant_type": "password",
 "username": "Fit-Indication-2067", # without u/
 "password": PASSWORD
 }

 resp2 = requests.post(
 "https://www.reddit.com/api/v1/access_token",
 auth=auth,
 data=data2,
 headers=headers
 )
 print(f"Status: {resp2.status_code}")

 # Test account info
 print("\n--- Test 3: Check if account exists ---")
 check_url = f"https://www.reddit.com/user/{USERNAME}/about.json"
 resp3 = requests.get(check_url, headers={"User-Agent": USER_AGENT})

 if resp3.status_code == 200:
 user_data = resp3.json()
 print(f" Account exists: /u/{USERNAME}")
 print(f"Account created: {user_data.get('data', {}).get('created_utc', 'Unknown')}")
 else:
 print(f" Could not verify account: {resp3.status_code}")

 # Suggest solutions
 print("\n=== Troubleshooting Steps ===")
 print("1. Verify the password is correct")
 print("2. Check if 2FA is enabled on the account (disable it for API access)")
 print("3. Try logging into reddit.com with username/password to verify")
 print("4. If account was created with Google, ensure a Reddit password is set:")
 print(" - Go to User Settings > Account > Change password")
 print("5. Consider creating an 'installed app' instead for read-only access")

if __name__ == "__main__":
 test_password_auth_debug()
