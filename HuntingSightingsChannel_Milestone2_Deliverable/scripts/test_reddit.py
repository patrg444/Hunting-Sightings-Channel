#!/usr/bin/env python3
"""
Test script to verify Reddit API is working with real data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from rich.console import Console
from rich.table import Table

console = Console()

def test_reddit_api():
 """Test Reddit API with real data."""
 console.print("[bold green]Testing Reddit API Connection...[/bold green]\n")

 # Create scraper instance
 scraper = RedditScraper()

 # Check if Reddit API was initialized
 if scraper.reddit:
 console.print(" Reddit API initialized successfully!")
 console.print(f" Using client ID: {os.getenv('REDDIT_CLIENT_ID')[:10]}...")
 else:
 console.print(" Reddit API failed to initialize. Using simulation mode.")
 return

 # Test fetching from a subreddit
 console.print("\n[bold]Testing subreddit access...[/bold]")
 try:
 # Get the 14ers subreddit
 subreddit = scraper.reddit.subreddit('14ers')
 console.print(f" Successfully accessed r/{subreddit.display_name}")
 console.print(f" Subscribers: {subreddit.subscribers:,}")

 # Get recent posts
 console.print("\n[bold]Recent posts from r/14ers:[/bold]")
 table = Table(show_header=True, header_style="bold magenta")
 table.add_column("Title", style="cyan", max_width=50)
 table.add_column("Author", style="green")
 table.add_column("Score", style="yellow")
 table.add_column("Comments", style="blue")

 for i, submission in enumerate(subreddit.new(limit=5)):
 table.add_row(
 submission.title[:50] + "..." if len(submission.title) > 50 else submission.title,
 str(submission.author),
 str(submission.score),
 str(submission.num_comments)
 )

 console.print(table)

 # Now test wildlife sighting extraction
 console.print("\n[bold]Testing wildlife sighting extraction...[/bold]")
 sightings = scraper.scrape(lookback_days=3)

 if sightings:
 console.print(f"\n Found {len(sightings)} wildlife sightings!")

 # Show first few sightings
 console.print("\n[bold]Sample sightings:[/bold]")
 for i, sighting in enumerate(sightings[:3]):
 console.print(f"\n[yellow]Sighting {i+1}:[/yellow]")
 console.print(f" Species: {sighting['species']}")
 console.print(f" Subreddit: r/{sighting['subreddit']}")
 console.print(f" Post: {sighting['reddit_post_title'][:60]}...")
 console.print(f" Context: {sighting['raw_text']}")
 console.print(f" URL: {sighting['source_url']}")
 else:
 console.print("\n No wildlife sightings found in recent posts")

 except Exception as e:
 console.print(f"\n Error accessing Reddit: {e}")

if __name__ == "__main__":
 test_reddit_api()
