#!/usr/bin/env python3
"""
Test Reddit scraper content extraction with improved keyword matching.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

def test_reddit_content():
 """Test Reddit content extraction with real API."""
 console.print("\n[bold cyan]Testing Reddit Content Extraction[/bold cyan]")
 console.print("=" * 50)

 # Initialize scraper
 scraper = RedditScraper()

 # Test if API is working
 if not scraper.reddit:
 console.print("[red] Reddit API not initialized - using simulation mode[/red]")
 return

 console.print("[green] Reddit API connected[/green]")

 # Get recent sightings
 console.print("\n[yellow]Fetching recent wildlife sightings...[/yellow]")
 sightings = scraper.scrape(lookback_days=7)

 console.print(f"\n[bold]Found {len(sightings)} wildlife sightings[/bold]")

 # Group by species
 species_counts = {}
 for sighting in sightings:
 species = sighting['species']
 species_counts[species] = species_counts.get(species, 0) + 1

 # Display species summary
 if species_counts:
 console.print("\n[bold cyan]Species Summary:[/bold cyan]")
 for species, count in sorted(species_counts.items()):
 console.print(f" • {species}: {count} sightings")

 # Show sample sightings
 console.print("\n[bold cyan]Sample Wildlife Sightings:[/bold cyan]")
 console.print("-" * 80)

 # Show up to 10 sightings
 for i, sighting in enumerate(sightings[:10], 1):
 console.print(f"\n[bold green]Sighting {i}:[/bold green]")
 console.print(f" [bold]Species:[/bold] {sighting['species']}")
 console.print(f" [bold]Keyword:[/bold] {sighting['keyword_matched']}")
 console.print(f" [bold]Subreddit:[/bold] r/{sighting.get('subreddit', 'unknown')}")
 console.print(f" [bold]Post:[/bold] {sighting.get('reddit_post_title', 'N/A')[:60]}...")
 console.print(f" [bold]Context:[/bold] {sighting['raw_text']}")
 console.print(f" [bold]URL:[/bold] {sighting['source_url']}")

 # Test specific examples to show improvement
 console.print("\n[bold cyan]Testing Keyword Matching Improvements:[/bold cyan]")
 console.print("-" * 80)

 test_texts = [
 ("I saw a bull elk near the treeline at dawn", True, "Should match - clear sighting"),
 ("We need to trim every gram of weight from our packs", False, "Should NOT match - 'gram' is not 'ram'"),
 ("The trail doesn't take up much room in the guidebook", False, "Should NOT match - 'room' context"),
 ("Spotted 6 mountain goats on the traverse", True, "Should match - number + animal"),
 ("Looking for elk during our trip next week", False, "Should NOT match - future tense"),
 ("Fresh bear tracks near the water source", True, "Should match - tracks indicate presence"),
 ("Deer Creek Trail is closed for maintenance", False, "Should NOT match - place name"),
 ("A herd of 20+ elk crossed the meadow", True, "Should match - clear sighting with herd"),
 ]

 # Test each example
 for text, should_match, reason in test_texts:
 sightings = scraper._extract_sightings_from_text(text, "test_url")
 matched = len(sightings) > 0

 status = "" if matched == should_match else ""
 console.print(f"\n{status} Text: \"{text}\"")
 console.print(f" Expected: {'Match' if should_match else 'No match'} - {reason}")
 console.print(f" Result: {'Matched' if matched else 'No match'}")
 if matched:
 console.print(f" Species: {sightings[0]['species']}, Keyword: {sightings[0]['keyword_matched']}")

if __name__ == "__main__":
 test_reddit_content()
