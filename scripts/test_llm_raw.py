#!/usr/bin/env python3
"""Test raw LLM response."""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

prompt = """
Analyze this text for a wildlife sighting of elk and extract any location information.
Posted in r/test

Text: "Saw a huge bull elk this morning at Bear Lake in Rocky Mountain National Park."

Return a JSON object with:
{
    "is_sighting": true/false,
    "confidence": 0-100,
    "location_name": null or specific place,
    "coordinates": null or [lat, lon],
    "location_confidence_radius": radius in miles
}

IMPORTANT: If a location name is mentioned, you MUST provide estimated coordinates:
- "Bear Lake in RMNP" → "coordinates": [40.3845, -105.6824]
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a wildlife sighting extractor. Always respond with valid JSON."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=200,
    temperature=0.1
)

print("Raw response:")
print(response.choices[0].message.content)