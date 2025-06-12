#!/usr/bin/env python3
"""
Test Reddit API using password authentication for script apps.
"""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_password_auth():
 """Test Reddit password authentication for script apps."""
 CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
 CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
 USERNAME = "Fit-Indication-2067"
 PASSWORD = "huntingsightingchannel"
 USER_AGENT = "script:HuntingSightingsBot:1.0 (by /u/Fit-Indication-2067)"

 print("=== Reddit Password Authentication Test ===")
 print(f"Client ID: {CLIENT_ID}")
 print(f"Client Secret: {CLIENT_SECRET[:10]}...")
 print(f"Username: {USERNAME}")
 print(f"User Agent: {USER_AGENT}")
 print()

 auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
 data = {
 "grant_type": "password",
 "username": USERNAME,
 "password": PASSWORD
 }
 headers = {"User-Agent": USER_AGENT}

 print("Requesting access token with password auth...")
 resp = requests.post(
 "https://www.reddit.com/api/v1/access_token",
 auth=auth,
 data=data,
 headers=headers
 )

 print(f"Status: {resp.status_code}")
 print(f"Response: {resp.json()}")

 if resp.status_code == 200:
 token_data = resp.json()
 access_token = token_data.get('access_token')
 print(f"\n Successfully obtained access token!")
 print(f"Token type: {token_data.get('token_type')}")
 print(f"Expires in: {token_data.get('expires_in')} seconds")
 print(f"Scope: {token_data.get('scope')}")

 # Test the token
 test_api_access(access_token, USER_AGENT)
 else:
 print(f"\n Authentication failed!")
 error_msg = resp.json()
 if 'error' in error_msg:
 print(f"Error: {error_msg.get('error')}")
 if error_msg.get('error') == 'invalid_grant':
 print("This usually means incorrect username/password or the account has 2FA enabled")

def test_api_access(access_token, user_agent):
 """Test API access with the token."""
 print("\n--- Testing API Access ---")

 # Test accessing r/14ers
 api_url = 'https://oauth.reddit.com/r/14ers/new'

 headers = {
 'Authorization': f'bearer {access_token}',
 'User-Agent': user_agent
 }

 try:
 response = requests.get(api_url, headers=headers, params={'limit': 5})
 print(f"API test status: {response.status_code}")

 if response.status_code == 200:
 data = response.json()
 posts = data.get('data', {}).get('children', [])
 print(f"\n API access successful!")
 print(f"Found {len(posts)} recent posts from r/14ers:")

 for post in posts:
 post_data = post.get('data', {})
 print(f"\n- Title: {post_data.get('title', 'N/A')[:60]}...")
 print(f" Author: u/{post_data.get('author', 'N/A')}")
 print(f" Score: {post_data.get('score', 0)}")

 # Test wildlife extraction
 print("\n--- Testing Wildlife Extraction ---")
 wildlife_keywords = ['elk', 'deer', 'bear', 'moose', 'goat', 'sheep', 'mountain lion', 'bighorn']
 wildlife_found = False

 for post in posts:
 post_data = post.get('data', {})
 text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}".lower()

 for keyword in wildlife_keywords:
 if keyword in text:
 wildlife_found = True
 print(f"\nFound wildlife mention in post:")
 print(f"Title: {post_data.get('title', 'N/A')}")
 print(f"Wildlife: {keyword}")
 break

 if not wildlife_found:
 print("\nNo wildlife mentions found in recent posts")

 else:
 print(f"\n API test failed!")
 print(f"Response: {response.text}")

 except Exception as e:
 print(f"Error during API test: {e}")

if __name__ == "__main__":
 test_password_auth()
