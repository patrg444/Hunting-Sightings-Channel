#!/usr/bin/env python3
"""
Test Reddit API using client_credentials for installed apps.
This works for read-only access to public data.
"""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_installed_app_auth():
 """Test Reddit installed app authentication."""
 CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
 CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
 USER_AGENT = "installed:HuntingSightingsBot:1.0 (by /u/Fit-Indication-2067)"

 print("=== Reddit Installed App Authentication Test ===")
 print(f"Client ID: {CLIENT_ID}")
 print(f"Client Secret: {CLIENT_SECRET[:10]}...")
 print(f"User Agent: {USER_AGENT}")
 print()

 auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
 data = {
 "grant_type": "client_credentials"
 }
 headers = {"User-Agent": USER_AGENT}

 print("Requesting access token...")
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
 else:
 print(f"\n API test failed!")
 print(f"Response: {response.text}")

 except Exception as e:
 print(f"Error during API test: {e}")

if __name__ == "__main__":
 test_installed_app_auth()
