#!/usr/bin/env python3
"""
Test Reddit location extraction on a large sample (150+ posts).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from rich.console import Console
from rich.table import Table
from rich.progress import track
import json
from collections import defaultdict

console = Console()

def test_large_sample():
 """Test location extraction on 150+ Reddit posts."""
 console.print("\n[bold cyan]Testing Reddit Location Extraction on Large Sample[/bold cyan]")
 console.print("=" * 80)

 # Initialize scraper
 scraper = RedditScraper()

 console.print(f"[bold]Reddit API:[/bold] {'Connected' if scraper.reddit else 'Simulation mode'}")
 console.print(f"[bold]LLM Validation:[/bold] {'Enabled' if scraper.validator.llm_available else 'Disabled'}")

 # Scrape more days to get 150+ sightings
 console.print("\n[bold]Scraping Reddit posts (this may take a few minutes)...[/bold]")

 # Start with 7 days and see how many we get
 all_sightings = []
 days = 7

 while len(all_sightings) < 150 and days <= 30:
 console.print(f"\nScraping last {days} days...")
 sightings = scraper.scrape(lookback_days=days)
 all_sightings = sightings # Replace, don't append (to avoid duplicates)
 console.print(f"Found {len(all_sightings)} sightings so far...")

 if len(all_sightings) < 150:
 days += 7

 # Limit to 200 for analysis (reasonable with rate limiting)
 sightings_to_analyze = all_sightings[:200]

 console.print(f"\n[bold green]Analyzing {len(sightings_to_analyze)} wildlife sightings[/bold green]")

 # Analyze location data
 location_stats = {
 'total': len(sightings_to_analyze),
 'with_any_location': 0,
 'with_gmu': 0,
 'with_county': 0,
 'with_coordinates': 0,
 'with_elevation': 0,
 'with_location_name': 0,
 'colorado_specific': 0
 }

 # Track unique values
 unique_gmus = set()
 unique_counties = set()
 unique_locations = set()
 elevations = []

 # Track by subreddit
 subreddit_stats = defaultdict(lambda: {'total': 0, 'with_location': 0})

 # Colorado keywords for identification
 colorado_keywords = ['colorado', 'gmu', 'unit', 'denver', 'boulder', 'aspen', 'vail',
 'durango', 'fort collins', 'colorado springs', 'rmnp', 'rocky mountain']

 # Analyze each sighting
 console.print("\n[bold]Processing sightings...[/bold]")
 for sighting in track(sightings_to_analyze, description="Analyzing..."):
 subreddit = sighting.get('subreddit', 'unknown')
 subreddit_stats[subreddit]['total'] += 1

 has_location = False

 # Check each location field
 if sighting.get('gmu_number'):
 location_stats['with_gmu'] += 1
 unique_gmus.add(str(sighting['gmu_number']))
 has_location = True

 if sighting.get('county'):
 location_stats['with_county'] += 1
 unique_counties.add(sighting['county'])
 has_location = True

 if sighting.get('coordinates'):
 location_stats['with_coordinates'] += 1
 has_location = True

 if sighting.get('elevation'):
 location_stats['with_elevation'] += 1
 elevations.append(sighting['elevation'])
 has_location = True

 if sighting.get('location_name'):
 location_stats['with_location_name'] += 1
 unique_locations.add(sighting['location_name'])
 has_location = True

 if has_location:
 location_stats['with_any_location'] += 1
 subreddit_stats[subreddit]['with_location'] += 1

 # Check if Colorado-specific
 all_text = ' '.join([
 str(sighting.get('location_name', '')),
 str(sighting.get('location_description', '')),
 str(sighting.get('county', '')),
 str(sighting.get('reddit_post_title', ''))
 ]).lower()

 if any(kw in all_text for kw in colorado_keywords) or sighting.get('gmu_number'):
 location_stats['colorado_specific'] += 1

 # Display results
 console.print("\n[bold cyan]Location Extraction Results[/bold cyan]")
 console.print("=" * 80)

 # Overall stats
 pct_with_location = (location_stats['with_any_location'] / location_stats['total'] * 100)
 console.print(f"\n[bold]Overall Statistics:[/bold]")
 console.print(f" Total sightings analyzed: {location_stats['total']}")
 console.print(f" Sightings with location data: {location_stats['with_any_location']} ({pct_with_location:.1f}%)")
 console.print(f" Colorado-specific sightings: {location_stats['colorado_specific']} ({location_stats['colorado_specific']/location_stats['total']*100:.1f}%)")

 # Location type breakdown
 console.print("\n[bold]Location Data Types Found:[/bold]")
 table = Table()
 table.add_column("Location Type", style="cyan")
 table.add_column("Count", style="green")
 table.add_column("Percentage", style="yellow")
 table.add_column("Unique Values", style="magenta")

 table.add_row("GMU Numbers",
 str(location_stats['with_gmu']),
 f"{location_stats['with_gmu']/location_stats['total']*100:.1f}%",
 str(len(unique_gmus)))

 table.add_row("Counties",
 str(location_stats['with_county']),
 f"{location_stats['with_county']/location_stats['total']*100:.1f}%",
 str(len(unique_counties)))

 table.add_row("Location Names",
 str(location_stats['with_location_name']),
 f"{location_stats['with_location_name']/location_stats['total']*100:.1f}%",
 str(len(unique_locations)))

 table.add_row("Coordinates",
 str(location_stats['with_coordinates']),
 f"{location_stats['with_coordinates']/location_stats['total']*100:.1f}%",
 "N/A")

 table.add_row("Elevations",
 str(location_stats['with_elevation']),
 f"{location_stats['with_elevation']/location_stats['total']*100:.1f}%",
 f"{min(elevations)}-{max(elevations)} ft" if elevations else "N/A")

 console.print(table)

 # Subreddit breakdown
 console.print("\n[bold]Location Data by Subreddit:[/bold]")
 sub_table = Table()
 sub_table.add_column("Subreddit", style="cyan")
 sub_table.add_column("Total Posts", style="green")
 sub_table.add_column("With Location", style="yellow")
 sub_table.add_column("Percentage", style="magenta")

 for sub, stats in sorted(subreddit_stats.items(), key=lambda x: x[1]['total'], reverse=True):
 pct = stats['with_location'] / stats['total'] * 100 if stats['total'] > 0 else 0
 sub_table.add_row(f"r/{sub}",
 str(stats['total']),
 str(stats['with_location']),
 f"{pct:.1f}%")

 console.print(sub_table)

 # Sample GMUs and locations
 if unique_gmus:
 console.print(f"\n[bold]GMU Numbers Found:[/bold] {', '.join(sorted(unique_gmus)[:10])}")
 if len(unique_gmus) > 10:
 console.print(f" ... and {len(unique_gmus) - 10} more")

 if unique_counties:
 console.print(f"\n[bold]Counties Found:[/bold] {', '.join(sorted(unique_counties)[:10])}")
 if len(unique_counties) > 10:
 console.print(f" ... and {len(unique_counties) - 10} more")

 if unique_locations:
 console.print(f"\n[bold]Sample Location Names:[/bold]")
 for loc in sorted(unique_locations)[:15]:
 console.print(f" • {loc}")
 if len(unique_locations) > 15:
 console.print(f" ... and {len(unique_locations) - 15} more")

 # Colorado-specific examples
 console.print("\n[bold cyan]Sample Colorado-Specific Sightings:[/bold cyan]")
 console.print("-" * 80)

 colorado_sightings = [s for s in sightings_to_analyze
 if any(kw in ' '.join([
 str(s.get('location_name', '')),
 str(s.get('location_description', '')),
 str(s.get('county', '')),
 str(s.get('reddit_post_title', ''))
 ]).lower() for kw in colorado_keywords) or s.get('gmu_number')]

 for i, sighting in enumerate(colorado_sightings[:5], 1):
 console.print(f"\n[bold green]Colorado Example {i}:[/bold green]")
 console.print(f" Species: {sighting.get('species', 'unknown')}")
 console.print(f" Subreddit: r/{sighting.get('subreddit', 'unknown')}")
 console.print(f" Title: {sighting.get('reddit_post_title', 'N/A')[:60]}...")

 if sighting.get('gmu_number'):
 console.print(f" [yellow]GMU: {sighting['gmu_number']}[/yellow]")
 if sighting.get('county'):
 console.print(f" [yellow]County: {sighting['county']}[/yellow]")
 if sighting.get('location_name'):
 console.print(f" [yellow]Location: {sighting['location_name']}[/yellow]")
 if sighting.get('elevation'):
 console.print(f" [yellow]Elevation: {sighting['elevation']} ft[/yellow]")

 # Save detailed results
 output_file = 'data/reddit_location_large_sample_results.json'
 with open(output_file, 'w') as f:
 json.dump({
 'stats': location_stats,
 'unique_gmus': list(unique_gmus),
 'unique_counties': list(unique_counties),
 'unique_locations': list(unique_locations)[:50], # Limit for file size
 'sample_colorado_sightings': colorado_sightings[:20]
 }, f, indent=2, default=str)

 console.print(f"\n[green]Detailed results saved to: {output_file}[/green]")

 # Summary
 console.print("\n[bold cyan]Summary:[/bold cyan]")
 console.print(f" {pct_with_location:.1f}% of wildlife sightings have location data")
 console.print(f" Found {len(unique_gmus)} unique GMU references")
 console.print(f" Found {len(unique_locations)} unique location names")
 console.print(f" {location_stats['colorado_specific']} Colorado-specific sightings identified")

if __name__ == "__main__":
 test_large_sample()
