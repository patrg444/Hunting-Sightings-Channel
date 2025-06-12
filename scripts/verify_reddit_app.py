#!/usr/bin/env python3
"""
Verify Reddit App setup and test basic API access.
"""

import os
import requests
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT')

print("Reddit App Details:")
print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret[:10]}...")
print(f"User Agent: {user_agent}")

# Test OAuth2 authentication
print("\nTesting OAuth2 authentication...")

# Reddit OAuth2 token endpoint
auth_url = 'https://www.reddit.com/api/v1/access_token'

# Create auth header
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)

# Request data for client credentials flow
data = {
 'grant_type': 'client_credentials'
}

# Headers
headers = {
 'User-Agent': user_agent
}

try:
 # Get access token
 response = requests.post(auth_url, auth=auth, data=data, headers=headers)
 print(f"\nToken request status: {response.status_code}")

 if response.status_code == 200:
 token_data = response.json()
 access_token = token_data['access_token']
 print(f" Access token obtained: {access_token[:20]}...")

 # Test API access with token
 api_headers = {
 'Authorization': f'bearer {access_token}',
 'User-Agent': user_agent
 }

 # Test getting subreddit info
 test_url = 'https://oauth.reddit.com/r/14ers/about.json'
 test_response = requests.get(test_url, headers=api_headers)
 print(f"\nAPI test status: {test_response.status_code}")

 if test_response.status_code == 200:
 data = test_response.json()
 print(f" Successfully accessed r/{data['data']['display_name']}")
 print(f" Subscribers: {data['data']['subscribers']:,}")
 else:
 print(f" API test failed: {test_response.text}")
 else:
 print(f" Token request failed: {response.text}")

except Exception as e:
 print(f"\n Error: {e}")
