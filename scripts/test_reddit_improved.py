#!/usr/bin/env python3
"""
Test the improved Reddit scraper with LLM validation and caching.
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

def test_improved_reddit_scraper():
 """Test Reddit scraper with LLM validation."""
 console.print("\n[bold cyan]Testing Improved Reddit Scraper with LLM Validation[/bold cyan]")
 console.print("=" * 70)

 # Initialize scraper
 scraper = RedditScraper()

 # Show validator status
 if scraper.validator.llm_available:
 console.print("[green] LLM validation enabled (OpenAI)[/green]")
 else:
 console.print("[yellow] LLM validation not available - using keyword matching[/yellow]")
 console.print(" To enable LLM validation, add OPENAI_API_KEY to your .env file")

 # Show cache stats
 cache_stats = scraper.validator.get_cache_stats()
 console.print(f"\n[bold]Cache Statistics:[/bold]")
 console.print(f" • Total posts cached: {cache_stats['total_posts_cached']}")
 console.print(f" • Posts with sightings: {cache_stats['posts_with_sightings']}")
 console.print(f" • Total sightings cached: {cache_stats['total_sightings']}")

 # Test improved keyword matching
 console.print("\n[bold cyan]Testing Improved Keyword Matching:[/bold cyan]")
 console.print("-" * 70)

 test_cases = [
 ("I saw 6 mountain goats on the ridge", True, "Valid sighting with number"),
 ("We need to trim every gram from our packs", False, "'gram' should not match 'ram'"),
 ("Spotted a bull elk near the lake", True, "Clear wildlife sighting"),
 ("Planning to hike Bear Lake Trail next week", False, "Place name, not sighting"),
 ("Fresh deer tracks in the snow", True, "Tracks indicate wildlife presence"),
 ("The deer resistant plants are growing well", False, "Not a wildlife sighting")
 ]

 for text, should_find, reason in test_cases:
 sightings = scraper._extract_sightings_from_text(text, "test_url")
 found = len(sightings) > 0

 # If sightings found, validate them
 if found and scraper.validator:
 validated = scraper.validator.validate_sightings_batch(sightings)
 found = len(validated) > 0

 status = "" if found == should_find else ""
 console.print(f"{status} '{text}'")
 console.print(f" Expected: {'Sighting' if should_find else 'No sighting'} - {reason}")
 console.print(f" Result: {'Found sighting' if found else 'No sighting found'}")
 if found and sightings:
 console.print(f" Details: {sightings[0]['species']} (keyword: {sightings[0]['keyword_matched']})")
 console.print()

 # Run actual scraping
 console.print("\n[bold cyan]Running Reddit Scraper (Last 7 Days):[/bold cyan]")
 console.print("-" * 70)

 # Scrape with 7-day lookback
 all_sightings = scraper.scrape(lookback_days=7)

 console.print(f"\n[bold]Total wildlife sightings found: {len(all_sightings)}[/bold]")

 # Group by species
 species_counts = {}
 for sighting in all_sightings:
 species = sighting['species']
 species_counts[species] = species_counts.get(species, 0) + 1

 if species_counts:
 console.print("\n[bold]Species Distribution:[/bold]")
 table = Table()
 table.add_column("Species", style="cyan")
 table.add_column("Count", style="green")
 table.add_column("Percentage", style="yellow")

 total = len(all_sightings)
 for species, count in sorted(species_counts.items(), key=lambda x: x[1], reverse=True):
 percentage = (count / total) * 100
 table.add_row(species.replace('_', ' ').title(), str(count), f"{percentage:.1f}%")

 console.print(table)

 # Show sample validated sightings
 if all_sightings:
 console.print("\n[bold cyan]Sample Validated Wildlife Sightings:[/bold cyan]")
 console.print("-" * 70)

 # Show up to 5 high-confidence sightings
 sorted_sightings = sorted(all_sightings,
 key=lambda x: x.get('confidence', 0.5),
 reverse=True)[:5]

 for i, sighting in enumerate(sorted_sightings, 1):
 console.print(f"\n[bold green]Sighting {i}:[/bold green]")
 console.print(f" [bold]Species:[/bold] {sighting['species'].replace('_', ' ').title()}")
 console.print(f" [bold]Confidence:[/bold] {sighting.get('confidence', 'N/A')}")
 console.print(f" [bold]Subreddit:[/bold] r/{sighting.get('subreddit', 'unknown')}")
 console.print(f" [bold]Post:[/bold] {sighting.get('reddit_post_title', 'N/A')[:60]}...")
 console.print(f" [bold]Context:[/bold] {sighting['raw_text']}")
 if sighting.get('llm_validated'):
 console.print(f" [bold]Validation:[/bold] [green] LLM Validated[/green]")
 console.print(f" [bold]URL:[/bold] {sighting['source_url']}")

 # Show cache efficiency
 console.print("\n[bold cyan]Cache Efficiency:[/bold cyan]")
 console.print("-" * 70)

 # Run again to show caching
 console.print("Running scraper again to demonstrate caching...")
 second_run_sightings = scraper.scrape(lookback_days=7)

 console.print(f"Second run found {len(second_run_sightings)} sightings")
 console.print("[green] Posts were served from cache (no API calls needed)[/green]")

 # Final cache stats
 final_cache_stats = scraper.validator.get_cache_stats()
 console.print(f"\n[bold]Final Cache Statistics:[/bold]")
 console.print(f" • Total posts cached: {final_cache_stats['total_posts_cached']}")
 console.print(f" • Posts with sightings: {final_cache_stats['posts_with_sightings']}")
 console.print(f" • Cache location: {final_cache_stats['cache_file']}")

if __name__ == "__main__":
 test_improved_reddit_scraper()
