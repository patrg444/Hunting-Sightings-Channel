#!/usr/bin/env python3
"""
Test the Reddit scraper with the new LLM-based location extraction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from rich.console import Console
from rich.table import Table
import json

console = Console()

def test_location_extraction():
 """Test Reddit scraper with location extraction."""
 console.print("\n[bold cyan]Testing Reddit Scraper with LLM Location Extraction[/bold cyan]")
 console.print("=" * 80)

 # Initialize scraper
 scraper = RedditScraper()

 # Show status
 console.print(f"[bold]Reddit API:[/bold] {'Connected' if scraper.reddit else 'Simulation mode'}")
 console.print(f"[bold]LLM Validation:[/bold] {'Enabled' if scraper.validator.llm_available else 'Disabled'}")

 # Run scraping for just 1 day to keep it fast
 console.print("\n[bold]Scraping Reddit posts from the last 24 hours...[/bold]")
 sightings = scraper.scrape(lookback_days=1)

 console.print(f"\n[bold]Total sightings found: {len(sightings)}[/bold]")

 # Analyze location data
 sightings_with_location = []
 location_types = {
 'gmu_number': [],
 'county': [],
 'location_name': [],
 'coordinates': [],
 'elevation': [],
 'location_description': []
 }

 for sighting in sightings:
 has_location = False
 for field in location_types.keys():
 if field in sighting and sighting[field]:
 has_location = True
 location_types[field].append({
 'value': sighting[field],
 'species': sighting.get('species', 'unknown'),
 'subreddit': sighting.get('subreddit', 'unknown')
 })

 if has_location:
 sightings_with_location.append(sighting)

 # Display summary
 console.print(f"\n[bold]Sightings with location data: {len(sightings_with_location)} / {len(sightings)} ({len(sightings_with_location)/len(sightings)*100:.1f}%)[/bold]")

 # Show location type breakdown
 console.print("\n[bold cyan]Location Data Found:[/bold cyan]")
 table = Table()
 table.add_column("Location Type", style="cyan")
 table.add_column("Count", style="green")
 table.add_column("Examples", style="yellow")

 for loc_type, values in location_types.items():
 if values:
 unique_values = list(set(str(v['value']) for v in values))
 examples = ", ".join(unique_values[:3])
 if len(unique_values) > 3:
 examples += f" (+{len(unique_values)-3} more)"
 table.add_row(loc_type.replace('_', ' ').title(), str(len(values)), examples)

 console.print(table)

 # Show detailed examples
 console.print("\n[bold cyan]Sample Sightings with Location Data:[/bold cyan]")
 console.print("-" * 80)

 for i, sighting in enumerate(sightings_with_location[:5], 1):
 console.print(f"\n[bold green]Example {i}:[/bold green]")
 console.print(f" [bold]Species:[/bold] {sighting.get('species', 'unknown')}")
 console.print(f" [bold]Confidence:[/bold] {sighting.get('confidence', 'N/A')}")
 console.print(f" [bold]Subreddit:[/bold] r/{sighting.get('subreddit', 'unknown')}")
 console.print(f" [bold]Title:[/bold] {sighting.get('reddit_post_title', 'N/A')[:60]}...")

 # Show location fields
 console.print(" [bold]Location Data:[/bold]")
 for field in ['gmu_number', 'county', 'location_name', 'coordinates', 'elevation', 'location_description']:
 if field in sighting and sighting[field]:
 console.print(f" • {field.replace('_', ' ').title()}: {sighting[field]}")

 console.print(f" [bold]Context:[/bold] {sighting.get('raw_text', 'N/A')[:150]}...")

 # Test specific examples with location keywords
 console.print("\n[bold cyan]Testing Specific Location Examples:[/bold cyan]")
 console.print("-" * 80)

 test_texts = [
 "Saw 6 elk in GMU 23 near Durango at 10,500 feet elevation",
 "Tagged out on a nice buck in unit 421 in Eagle County",
 "Bear tracks on the Maroon Bells trail at treeline",
 "Glassed a herd near Pagosa Springs in the Weminuche Wilderness"
 ]

 for text in test_texts:
 console.print(f"\n[bold]Test text:[/bold] '{text}'")

 # Test direct validation
 is_valid, confidence, location_data = scraper.validator.validate_sighting_with_llm(
 text,
 "elk" if "elk" in text else "deer" if "buck" in text else "bear",
 "elk" if "elk" in text else "deer" if "buck" in text else "bear"
 )

 console.print(f" Valid sighting: {'' if is_valid else ''} (confidence: {confidence:.2f})")
 if location_data:
 console.print(" Location extracted:")
 for k, v in location_data.items():
 console.print(f" • {k}: {v}")

 # Save results
 output_file = 'data/reddit_location_test_results.json'
 with open(output_file, 'w') as f:
 json.dump({
 'total_sightings': len(sightings),
 'sightings_with_location': len(sightings_with_location),
 'location_types': {k: len(v) for k, v in location_types.items() if v},
 'sample_sightings': sightings_with_location[:10]
 }, f, indent=2, default=str)

 console.print(f"\n[green]Results saved to: {output_file}[/green]")

if __name__ == "__main__":
 test_location_extraction()
