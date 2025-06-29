#!/usr/bin/env python3
"""Debug OpenAI API connection."""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Test OpenAI directly
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("Testing OpenAI API...")
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in JSON format: {\"message\": \"hello\"}"}
        ],
        max_tokens=50,
        temperature=0.1
    )
    
    print(f"Response: {response}")
    print(f"Content: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()