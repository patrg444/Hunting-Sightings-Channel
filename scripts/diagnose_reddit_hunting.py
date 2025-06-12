#!/usr/bin/env python3
"""
Diagnose why we're finding so few wildlife sightings in hunting subreddits.
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

def diagnose_hunting_content():
    """Analyze Reddit hunting content to understand sighting detection."""
    console.print("\n[bold cyan]Reddit Hunting Content Diagnostic[/bold cyan]")
    console.print("=" * 70)
    
    # Initialize scraper
    scraper = RedditScraper()
    
    if not scraper.reddit:
        console.print("[red]Reddit API not available[/red]")
        return
    
    # Check cache to see what's really there
    console.print("\n[bold yellow]Analyzing Cache Contents[/bold yellow]")
    cache_file = "data/cache/parsed_posts.json"
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        
        console.print(f"Total cached posts: {len(cache)}")
        
        # Find posts with wildlife mentions
        posts_with_wildlife = 0
        example_posts = []
        
        for post_id, data in cache.items():
            # Skip if it's parsed_date is missing (old format)
            if 'sightings' in data and len(data['sightings']) > 0:
                posts_with_wildlife += 1
                if len(example_posts) < 5:
                    example_posts.append((post_id, data))
        
        console.print(f"Posts with sightings: {posts_with_wildlife}")
        
        # Show examples
        if example_posts:
            console.print("\n[bold]Example Posts with Sightings:[/bold]")
            for post_id, data in example_posts:
                console.print(f"\n[green]Post ID: {post_id}[/green]")
                console.print(f"Sighting count: {data['sighting_count']}")
                for s in data['sightings'][:2]:
                    console.print(f"  - {s.get('species', 'unknown')}: {s.get('raw_text', '')[:100]}...")
    
    # Now let's manually check some hunting posts
    console.print("\n[bold yellow]Manually Checking r/cohunting Posts[/bold yellow]")
    console.print("-" * 70)
    
    # Expanded wildlife keywords including hunting terms
    hunting_keywords = [
        'elk', 'deer', 'bear', 'goat', 'sheep', 'moose', 'lion', 'bobcat',
        'bull', 'cow', 'buck', 'doe', 'tag', 'harvest', 'shot', 'archery',
        'rifle', 'hunt', 'scouting', 'glassing', 'bugle', 'rut', 'shed'
    ]
    
    try:
        subreddit = scraper.reddit.subreddit('cohunting')
        posts_analyzed = 0
        posts_with_keywords = 0
        
        for submission in subreddit.new(limit=20):
            posts_analyzed += 1
            full_text = f"{submission.title} {submission.selftext}".lower()
            
            # Check for any hunting/wildlife keywords
            found_keywords = [kw for kw in hunting_keywords if kw in full_text]
            
            if found_keywords:
                posts_with_keywords += 1
                console.print(f"\n[green]Post {posts_analyzed}: Contains keywords: {', '.join(found_keywords)}[/green]")
                console.print(f"Title: {submission.title}")
                console.print(f"Text preview: {submission.selftext[:200]}..." if submission.selftext else "[No text]")
                
                # Test extraction methods
                console.print("\n[yellow]Testing extraction methods:[/yellow]")
                
                # Method 1: Old extraction
                old_sightings = scraper._extract_sightings_from_text(full_text, submission.url)
                console.print(f"  Old method found: {len(old_sightings)} sightings")
                
                # Method 2: New simplified extraction
                new_mentions = scraper._extract_potential_wildlife_mentions(full_text, submission.url)
                console.print(f"  New method found: {len(new_mentions)} potential mentions")
                
                if new_mentions:
                    console.print(f"  Species mentioned: {new_mentions[0]['species_mentioned']}")
                
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"Posts analyzed: {posts_analyzed}")
        console.print(f"Posts with wildlife/hunting keywords: {posts_with_keywords} ({posts_with_keywords/posts_analyzed*100:.1f}%)")
        
    except Exception as e:
        console.print(f"[red]Error analyzing r/cohunting: {e}[/red]")

if __name__ == "__main__":
    diagnose_hunting_content()
