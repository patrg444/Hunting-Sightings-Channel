#!/usr/bin/env python3
"""
Diagnose what content is actually in Reddit posts to understand why no sightings are found.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import json

console = Console()

def diagnose_reddit_content():
    """Analyze Reddit content to understand sighting detection."""
    console.print("\n[bold cyan]Reddit Content Diagnostic[/bold cyan]")
    console.print("=" * 70)
    
    # Initialize scraper
    scraper = RedditScraper()
    
    if not scraper.reddit:
        console.print("[red]Reddit API not available[/red]")
        return
    
    # Wildlife keywords to search for
    wildlife_keywords = ['elk', 'deer', 'bear', 'goat', 'sheep', 'moose', 'lion', 'bobcat']
    
    # Check each subreddit
    for subreddit_name in ['14ers', 'coloradohikers']:
        console.print(f"\n[bold yellow]Analyzing r/{subreddit_name}[/bold yellow]")
        console.print("-" * 70)
        
        try:
            subreddit = scraper.reddit.subreddit(subreddit_name)
            posts_with_wildlife = 0
            
            # Get recent posts
            for i, submission in enumerate(subreddit.new(limit=10)):
                full_text = f"{submission.title} {submission.selftext}".lower()
                
                # Check if any wildlife keywords present
                found_keywords = [kw for kw in wildlife_keywords if kw in full_text]
                
                if found_keywords:
                    posts_with_wildlife += 1
                    console.print(f"\n[green]Post {i+1} - Contains wildlife keywords: {', '.join(found_keywords)}[/green]")
                    console.print(f"Title: {submission.title}")
                    console.print(f"Preview: {submission.selftext[:150]}..." if submission.selftext else "[No text content]")
                    
                    # Try extraction
                    sightings = scraper._extract_sightings_from_text(full_text, submission.url)
                    console.print(f"Raw extractions: {len(sightings)} found")
                    
                    if sightings:
                        # Try validation
                        validated = scraper.validator.validate_sightings_batch(sightings)
                        console.print(f"After validation: {len(validated)} remain")
                        
                        if validated:
                            for s in validated[:2]:  # Show first 2
                                console.print(f"  - {s['species']}: '{s['raw_text']}'")
                else:
                    if i < 3:  # Show first 3 posts without wildlife
                        console.print(f"\n[dim]Post {i+1} - No wildlife keywords[/dim]")
                        console.print(f"[dim]Title: {submission.title}[/dim]")
            
            console.print(f"\n[bold]Summary: {posts_with_wildlife}/10 posts contain wildlife keywords[/bold]")
            
        except Exception as e:
            console.print(f"[red]Error analyzing r/{subreddit_name}: {e}[/red]")
    
    # Check the cache to see what was processed
    console.print("\n[bold cyan]Cache Analysis:[/bold cyan]")
    console.print("-" * 70)
    
    cache_file = "data/cache/parsed_posts.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        
        # Count posts with wildlife keywords in cache
        posts_with_keywords = 0
        example_texts = []
        
        for post_id, data in list(cache.items())[:50]:  # Check first 50
            if 'content_hash' in data:
                # Can't see original content, but check sighting count
                if data.get('sighting_count', 0) > 0:
                    posts_with_keywords += 1
        
        console.print(f"Cache contains {len(cache)} posts")
        console.print(f"Posts marked as having sightings: {posts_with_keywords}")

if __name__ == "__main__":
    diagnose_reddit_content()
