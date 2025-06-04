#!/usr/bin/env python3
"""
Debug script for Reddit API authentication.
"""

import os
import praw
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"REDDIT_CLIENT_ID: {os.getenv('REDDIT_CLIENT_ID')}")
print(f"REDDIT_CLIENT_SECRET: {os.getenv('REDDIT_CLIENT_SECRET')[:10]}...")
print(f"REDDIT_USER_AGENT: {os.getenv('REDDIT_USER_AGENT')}")

try:
    # Create Reddit instance
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT')
    )
    
    print("\nReddit instance created.")
    
    # Test basic functionality
    print(f"Read-only mode: {reddit.read_only}")
    
    # Try to get a subreddit
    subreddit = reddit.subreddit("14ers")
    print(f"\nSubreddit: r/{subreddit.display_name}")
    
    # Try to get the subreddit's title (doesn't require authentication)
    print(f"Title: {subreddit.title}")
    
    # Try to get a post
    print("\nGetting recent posts...")
    for i, submission in enumerate(subreddit.new(limit=3)):
        print(f"{i+1}. {submission.title[:60]}...")
        
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
