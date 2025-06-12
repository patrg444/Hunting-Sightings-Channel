#!/usr/bin/env python3
"""
Direct test of Reddit OAuth2 authentication without using PRAW.
This will help determine if the issue is with PRAW or with the credentials.
"""

import requests
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_reddit_oauth():
 """Test Reddit OAuth2 authentication directly."""
 client_id = os.getenv('REDDIT_CLIENT_ID')
 client_secret = os.getenv('REDDIT_CLIENT_SECRET')
 user_agent = os.getenv('REDDIT_USER_AGENT')

 print(f"Testing Reddit OAuth2 with:")
 print(f"Client ID: {client_id}")
 print(f"Client Secret: {client_secret[:10]}...")
 print(f"User Agent: {user_agent}")
 print()

 # Reddit OAuth2 token endpoint
 auth_url = 'https://www.reddit.com/api/v1/access_token'

 # Basic auth header (client_id:client_secret in base64)
 auth_string = f"{client_id}:{client_secret}"
 auth_bytes = auth_string.encode('ascii')
 auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

 headers = {
 'Authorization': f'Basic {auth_b64}',
 'User-Agent': user_agent,
 'Content-Type': 'application/x-www-form-urlencoded'
 }

 # Request body for client credentials grant
 data = {
 'grant_type': 'client_credentials'
 }

 print("Sending OAuth2 token request...")
 try:
 response = requests.post(auth_url, headers=headers, data=data)
 print(f"Response status: {response.status_code}")
 print(f"Response headers: {dict(response.headers)}")
 print(f"Response body: {response.text}")

 if response.status_code == 200:
 token_data = response.json()
 access_token = token_data.get('access_token')
 print(f"\n Successfully obtained access token!")
 print(f"Token type: {token_data.get('token_type')}")
 print(f"Expires in: {token_data.get('expires_in')} seconds")
 print(f"Scope: {token_data.get('scope')}")

 # Test the token by making an API request
 test_api_request(access_token, user_agent)
 else:
 print(f"\n Authentication failed!")
 print(f"Error response: {response.text}")

 except Exception as e:
 print(f"Error during authentication: {e}")

def test_api_request(access_token, user_agent):
 """Test the access token with a simple API request."""
 print("\n--- Testing API Access ---")

 # Test endpoint - get info about r/test subreddit
 api_url = 'https://oauth.reddit.com/r/test/about'

 headers = {
 'Authorization': f'bearer {access_token}',
 'User-Agent': user_agent
 }

 try:
 response = requests.get(api_url, headers=headers)
 print(f"API test status: {response.status_code}")

 if response.status_code == 200:
 data = response.json()
 subreddit = data.get('data', {})
 print(f"\n API access successful!")
 print(f"Subreddit: r/{subreddit.get('display_name')}")
 print(f"Subscribers: {subreddit.get('subscribers')}")
 else:
 print(f"\n API test failed!")
 print(f"Response: {response.text}")

 except Exception as e:
 print(f"Error during API test: {e}")

if __name__ == "__main__":
 test_reddit_oauth()
