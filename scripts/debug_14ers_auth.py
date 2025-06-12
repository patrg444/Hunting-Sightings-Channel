#!/usr/bin/env python3
"""
Debug script to investigate 14ers.com authentication issues.
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from loguru import logger

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def debug_login():
    """Debug the login process step by step."""
    BASE_URL = "https://www.14ers.com"
    login_page_url = f"{BASE_URL}/php14ers/loginviaforum.php"
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Step 1: Get login page
    logger.info("Step 1: Fetching login page...")
    response = session.get(login_page_url)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Cookies: {list(session.cookies)}")
    
    # Parse the page
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form', id='loginForm')
    
    if not form:
        logger.error("Could not find login form!")
        return
    
    # Extract form details
    action = form.get('action', '')
    logger.info(f"Form action: {action}")
    
    # Extract all form fields
    login_data = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        value = inp.get('value', '')
        input_type = inp.get('type', 'text')
        
        if name:
            if input_type != 'password':
                logger.info(f"Field '{name}' (type={input_type}): {value[:50]}...")
            else:
                logger.info(f"Field '{name}' (type={input_type}): [HIDDEN]")
                
            if input_type == 'hidden':
                login_data[name] = value
    
    # Add credentials
    login_data['username'] = 'nicholasreichert86'
    login_data['password'] = 'Huntingsightingchannel86'
    login_data['autologin'] = 'on'
    
    # Build login URL
    if action.startswith('../'):
        login_post_url = f"{BASE_URL}/{action[3:]}"
    elif action.startswith('/'):
        login_post_url = f"{BASE_URL}{action}"
    else:
        login_post_url = action
        
    logger.info(f"\nStep 2: Attempting login to {login_post_url}")
    logger.info(f"Sending fields: {list(login_data.keys())}")
    
    # Attempt login
    response = session.post(
        login_post_url,
        data=login_data,
        allow_redirects=False,  # Don't follow redirects to see what happens
        headers={
            'Referer': login_page_url,
            'Origin': BASE_URL
        }
    )
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    
    # Check for redirects
    if 'Location' in response.headers:
        logger.info(f"Redirect to: {response.headers['Location']}")
        
        # Follow the redirect
        redirect_url = response.headers['Location']
        if not redirect_url.startswith('http'):
            redirect_url = f"{BASE_URL}/{redirect_url}"
            
        response = session.get(redirect_url)
        logger.info(f"Final status: {response.status_code}")
    
    # Check response content
    response_text = response.text.lower()
    
    # Save response for inspection
    with open('login_response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    logger.info("Saved response to login_response.html")
    
    # Check for success/failure indicators
    if 'logout' in response_text or 'log out' in response_text:
        logger.success("Login appears successful - found logout link")
    elif 'incorrect' in response_text or 'invalid' in response_text:
        logger.error("Login failed - incorrect credentials message found")
        
        # Try to find the error message
        soup = BeautifulSoup(response.text, 'html.parser')
        error_divs = soup.find_all(['div', 'p'], class_=['error', 'message', 'alert'])
        for div in error_divs:
            logger.error(f"Error message: {div.get_text(strip=True)}")
    elif 'username' in response_text and 'password' in response_text:
        logger.warning("Still on login page")
    else:
        logger.info("Response unclear - check login_response.html")
        
    # Test accessing a protected page
    logger.info("\nStep 3: Testing access to trip reports page...")
    test_url = f"{BASE_URL}/php14ers/tripmain.php"
    response = session.get(test_url)
    
    if response.status_code == 200:
        if 'resultsTable' in response.text:
            logger.success("Can access trip reports - login might be successful!")
        else:
            logger.warning("Got trip reports page but content looks different")
    else:
        logger.error(f"Cannot access trip reports - status {response.status_code}")


if __name__ == "__main__":
    debug_login()
