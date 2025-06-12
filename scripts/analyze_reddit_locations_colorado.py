#!/usr/bin/env python3
"""
Analyze Reddit posts specifically for Colorado location data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from rich.console import Console
from rich.table import Table
import json
import praw
from openai import OpenAI

console = Console()

def get_full_post_text(post_id: str) -> tuple:
 """Get full text of a Reddit post using the API."""
 try:
 reddit = praw.Reddit(
 client_id=os.getenv('REDDIT_CLIENT_ID'),
 client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
 user_agent=os.getenv('REDDIT_USER_AGENT'),
 check_for_async=False
 )
 reddit.read_only = True

 submission = reddit.submission(id=post_id)
 return submission.title, submission.selftext
 except Exception as e:
 console.print(f"[yellow]Error fetching full post: {e}[/yellow]")
 return None, None

def analyze_colorado_locations():
 """Focus on Colorado-specific location analysis."""

 console.print("\n[bold cyan]Analyzing Reddit Posts for Colorado Location Data[/bold cyan]")
 console.print("=" * 80)

 # Initialize components
 scraper = RedditScraper()

 if not os.getenv('OPENAI_API_KEY'):
 console.print("[red]Error: OpenAI API key not configured[/red]")
 return

 client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

 # Get recent sightings
 console.print("\nFetching recent Reddit sightings...")
 all_sightings = scraper.scrape(lookback_days=7)

 # Filter for Colorado-related posts
 colorado_keywords = ['colorado', 'gmu', 'unit', 'rocky mountain', 'rmnp', 'denver',
 'boulder', 'aspen', 'vail', 'summit county', 'eagle county']

 colorado_sightings = []
 for sighting in all_sightings:
 title = sighting.get('reddit_post_title', '').lower()
 text = sighting.get('raw_text', '').lower()
 sub = sighting.get('subreddit', '').lower()

 # Check if Colorado-related
 if (any(kw in title + text for kw in colorado_keywords) or
 sub in ['cohunting', 'colorado', 'coloradosprings', 'rmnp', 'coloradohikers']):
 colorado_sightings.append(sighting)

 console.print(f"Found {len(colorado_sightings)} Colorado-related sightings")

 # Analyze first 15 Colorado posts for location data
 location_analysis = []
 posts_to_analyze = colorado_sightings[:15]

 for i, sighting in enumerate(posts_to_analyze, 1):
 console.print(f"\n[bold]Analyzing Colorado post {i}/{len(posts_to_analyze)}...[/bold]")

 # Try to get full post text
 post_id = sighting.get('post_id', '')
 full_title, full_text = get_full_post_text(post_id) if post_id else (None, None)

 # Use full text if available, otherwise use cached snippet
 if full_title and full_text:
 post_title = full_title
 content = full_text[:1000] # Limit to 1000 chars
 console.print(f"[green]Using full post text[/green]")
 else:
 post_title = sighting.get('reddit_post_title', '')
 content = sighting.get('raw_text', '')
 console.print(f"[yellow]Using cached snippet[/yellow]")

 subreddit = sighting.get('subreddit', '')

 # Construct analysis prompt
 prompt = f"""Analyze this Colorado-related Reddit post for location information.

Post from r/{subreddit}:
Title: {post_title}
Content: {content}

Extract Colorado-specific location mentions:
1. GMU/Unit numbers (e.g., "GMU 12", "Unit 23", "unit 421")
2. Colorado counties (e.g., "Eagle County", "Summit County")
3. Colorado trails, peaks, or passes (e.g., "Mt. Elbert", "Maroon Bells")
4. Colorado towns/cities (e.g., "Durango", "Leadville", "Pagosa Springs")
5. GPS coordinates or lat/long
6. Colorado wilderness areas or parks (e.g., "Flat Tops", "Weminuche")
7. Colorado landmarks (e.g., "Twin Lakes", "Taylor Park")
8. Elevation or elevation ranges

Return a JSON object with:
- gmu_numbers: list of GMU/unit numbers (extract just the number)
- counties: list of Colorado county names
- trails_peaks: list of trail/peak/pass names
- towns_cities: list of Colorado town/city names
- coordinates: list of GPS coordinates
- wilderness_areas: list of wilderness/park names
- landmarks: list of other Colorado geographic features
- elevation_mentions: list of elevation references
- location_summary: brief summary of Colorado location info
- has_specific_location: true if contains specific Colorado location data
- confidence: your confidence in the location extraction (0-100)
"""

 try:
 response = client.chat.completions.create(
 model="gpt-3.5-turbo",
 messages=[
 {"role": "system", "content": "You are a Colorado geography expert. Extract only verified Colorado locations. Always respond with valid JSON."},
 {"role": "user", "content": prompt}
 ],
 max_tokens=400,
 temperature=0.1
 )

 result = response.choices[0].message.content.strip()
 location_data = json.loads(result)
 location_data['post_title'] = post_title[:80] + "..."
 location_data['subreddit'] = subreddit
 location_data['species'] = sighting.get('species', 'unknown')
 location_data['post_id'] = post_id
 location_analysis.append(location_data)
 except json.JSONDecodeError as e:
 console.print(f"[red]JSON parse error: {e}[/red]")
 except Exception as e:
 console.print(f"[red]Error: {e}[/red]")

 # Display results
 console.print("\n[bold cyan]Colorado Location Data Analysis Results[/bold cyan]")
 console.print("=" * 80)

 # Summary statistics
 total_with_location = sum(1 for loc in location_analysis if loc.get('has_specific_location'))
 high_confidence = sum(1 for loc in location_analysis if loc.get('confidence', 0) >= 80)

 console.print(f"\n[bold]Posts with specific Colorado locations: {total_with_location}/{len(location_analysis)}[/bold]")
 console.print(f"[bold]High confidence extractions (80%+): {high_confidence}[/bold]")

 # Location type frequency
 location_types = {
 'GMU Numbers': [],
 'Counties': [],
 'Trails/Peaks': [],
 'Towns/Cities': [],
 'Wilderness Areas': [],
 'Landmarks': [],
 'Elevations': []
 }

 for loc in location_analysis:
 if loc.get('gmu_numbers'):
 location_types['GMU Numbers'].extend(loc['gmu_numbers'])
 if loc.get('counties'):
 location_types['Counties'].extend(loc['counties'])
 if loc.get('trails_peaks'):
 location_types['Trails/Peaks'].extend(loc['trails_peaks'])
 if loc.get('towns_cities'):
 location_types['Towns/Cities'].extend(loc['towns_cities'])
 if loc.get('wilderness_areas'):
 location_types['Wilderness Areas'].extend(loc['wilderness_areas'])
 if loc.get('landmarks'):
 location_types['Landmarks'].extend(loc['landmarks'])
 if loc.get('elevation_mentions'):
 location_types['Elevations'].extend(loc['elevation_mentions'])

 # Display location type summary
 console.print("\n[bold]Colorado Location Types Found:[/bold]")
 table = Table()
 table.add_column("Location Type", style="cyan")
 table.add_column("Count", style="green")
 table.add_column("Examples", style="yellow")

 for loc_type, values in location_types.items():
 if values:
 unique_values = list(set(values))
 examples = ", ".join(str(v) for v in unique_values[:3])
 if len(unique_values) > 3:
 examples += f" (+{len(unique_values)-3} more)"
 table.add_row(loc_type, str(len(values)), examples)

 console.print(table)

 # Show detailed examples
 console.print("\n[bold cyan]Sample Colorado Posts with Location Data:[/bold cyan]")
 console.print("-" * 80)

 posts_with_location = sorted(
 [loc for loc in location_analysis if loc.get('has_specific_location')],
 key=lambda x: x.get('confidence', 0),
 reverse=True
 )[:5]

 for i, loc in enumerate(posts_with_location, 1):
 console.print(f"\n[bold green]Example {i}:[/bold green]")
 console.print(f" [bold]Confidence:[/bold] {loc.get('confidence', 'N/A')}%")
 console.print(f" [bold]Subreddit:[/bold] r/{loc['subreddit']}")
 console.print(f" [bold]Species:[/bold] {loc['species']}")
 console.print(f" [bold]Title:[/bold] {loc['post_title']}")
 console.print(f" [bold]Summary:[/bold] {loc.get('location_summary', 'N/A')}")

 if loc.get('gmu_numbers'):
 console.print(f" [bold]GMU Numbers:[/bold] {', '.join(str(g) for g in loc['gmu_numbers'])}")
 if loc.get('counties'):
 console.print(f" [bold]Counties:[/bold] {', '.join(loc['counties'])}")
 if loc.get('trails_peaks'):
 console.print(f" [bold]Trails/Peaks:[/bold] {', '.join(loc['trails_peaks'])}")
 if loc.get('towns_cities'):
 console.print(f" [bold]Towns/Cities:[/bold] {', '.join(loc['towns_cities'])}")
 if loc.get('wilderness_areas'):
 console.print(f" [bold]Wilderness:[/bold] {', '.join(loc['wilderness_areas'])}")

 # Save analysis
 output_file = 'data/reddit_colorado_location_analysis.json'
 with open(output_file, 'w') as f:
 json.dump(location_analysis, f, indent=2)

 console.print(f"\n[green]Full analysis saved to: {output_file}[/green]")

 # Summary recommendations
 console.print("\n[bold cyan]Location Extraction Insights:[/bold cyan]")
 console.print("-" * 80)

 if location_types['GMU Numbers']:
 console.print(f" Found {len(set(location_types['GMU Numbers']))} unique GMU references")
 else:
 console.print(" No GMU numbers found - regex extraction would help")

 if location_types['Counties']:
 console.print(f" Found {len(set(location_types['Counties']))} Colorado counties")

 if location_types['Trails/Peaks']:
 console.print(f" Found {len(set(location_types['Trails/Peaks']))} trails/peaks")

 console.print("\n[yellow]Recommendation:[/yellow] Implement regex patterns for GMU extraction")
 console.print("and geocoding for place names to get coordinates.")

if __name__ == "__main__":
 analyze_colorado_locations()
