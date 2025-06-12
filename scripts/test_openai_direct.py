#!/usr/bin/env python3
"""
Direct test of OpenAI API to diagnose initialization issues.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Clear all proxy variables before import
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
 'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
for var in proxy_vars:
 if var in os.environ:
 del os.environ[var]

# Now import and test OpenAI
try:
 from openai import OpenAI

 # Get API key
 api_key = os.getenv('OPENAI_API_KEY')
 if not api_key:
 print(" No OpenAI API key found in environment")
 exit(1)

 print(f" API key found: {api_key[:10]}...")

 # Try to create client
 client = OpenAI(api_key=api_key)
 print(" OpenAI client created successfully")

 # Test a simple API call
 response = client.chat.completions.create(
 model="gpt-3.5-turbo",
 messages=[
 {"role": "user", "content": "Is 'saw an elk' a wildlife sighting? Reply YES or NO"}
 ],
 max_tokens=10
 )

 result = response.choices[0].message.content
 print(f" API call successful! Response: {result}")

except Exception as e:
 print(f" Error: {e}")
 import traceback
 traceback.print_exc()
