#!/usr/bin/env python3
"""
Detailed debugging of Reddit OAuth2 authentication.
"""

import requests
import base64
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def debug_reddit_auth():
    """Debug Reddit OAuth2 authentication with detailed output."""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')
    
    print("=== Reddit OAuth2 Debug ===")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret}")
    print(f"Client Secret length: {len(client_secret) if client_secret else 0}")
    print(f"User Agent: {user_agent}")
    
    # Check for any hidden characters or issues
    print(f"\nClient ID bytes: {client_id.encode() if client_id else None}")
    print(f"Client Secret bytes: {client_secret.encode() if client_secret else None}")
    
    # Test different authentication methods
    print("\n=== Testing Authentication Methods ===")
    
    # Method 1: Using requests auth parameter
    print("\n1. Using requests.auth.HTTPBasicAuth:")
    from requests.auth import HTTPBasicAuth
    
    auth_url = 'https://www.reddit.com/api/v1/access_token'
    headers = {
        'User-Agent': user_agent
    }
    data = {
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(
            auth_url,
            auth=HTTPBasicAuth(client_id, client_secret),
            data=data,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Manual Basic auth header
    print("\n2. Using manual Basic auth header:")
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    print(f"Auth string: {client_id}:{'*' * len(client_secret)}")
    print(f"Base64 encoded: {auth_b64[:20]}...")
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'User-Agent': user_agent,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Print request details for debugging
        print(f"\nRequest headers sent:")
        for k, v in response.request.headers.items():
            if k.lower() == 'authorization':
                print(f"  {k}: {v[:20]}...")
            else:
                print(f"  {k}: {v}")
                
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with curl command for comparison
    print("\n=== Equivalent curl command ===")
    curl_cmd = f'''curl -X POST https://www.reddit.com/api/v1/access_token \\
    -H "User-Agent: {user_agent}" \\
    -u "{client_id}:{client_secret}" \\
    -d "grant_type=client_credentials"'''
    print(curl_cmd)
    
    # Check if credentials match what's shown in the Reddit app
    print("\n=== Credential Verification ===")
    print("Please verify these match your Reddit app:")
    print(f"Client ID should be: {client_id}")
    print(f"This is the value shown under 'personal use script' in your Reddit app")
    print(f"\nClient Secret should be: {client_secret}")
    print(f"This is the 'secret' value in your Reddit app")

if __name__ == "__main__":
    debug_reddit_auth()
