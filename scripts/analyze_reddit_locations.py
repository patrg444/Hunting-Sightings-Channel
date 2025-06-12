#!/usr/bin/env python3
"""
Analyze Reddit posts to identify what location data is available using LLM.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from scrapers.llm_validator import LLMValidator
from rich.console import Console
from rich.table import Table
import json
import os
from openai import OpenAI

console = Console()

def analyze_location_content():
    """Use LLM to analyze what location information is present in Reddit posts."""
    
    console.print("\n[bold cyan]Analyzing Reddit Posts for Location Data[/bold cyan]")
    console.print("=" * 80)
    
    # Initialize components
    scraper = RedditScraper()
    
    # Initialize OpenAI directly
    if not os.getenv('OPENAI_API_KEY'):
        console.print("[red]Error: OpenAI API key not configured[/red]")
        return
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Get recent sightings
    console.print("\nFetching recent Reddit sightings...")
    sightings = scraper.scrape(lookback_days=7)[:20]  # Analyze 20 recent posts
    
    location_analysis = []
    
    for i, sighting in enumerate(sightings, 1):
        console.print(f"\n[bold]Analyzing post {i}/20...[/bold]")
        
        # Get the full post text
        post_title = sighting.get('reddit_post_title', '')
        raw_text = sighting.get('raw_text', '')
        subreddit = sighting.get('subreddit', '')
        
        # Construct full context
        full_text = f"Title: {post_title}\nContent: {raw_text}"
        
        # Analyze with LLM for location data
        prompt = f"""Analyze this Reddit post for location information. Extract any mentions of:
1. GMU numbers (e.g., "GMU 12", "Unit 23")
2. Colorado counties
3. Specific trails or peaks
4. Towns or cities
5. GPS coordinates
6. Elevation ranges
7. Landmarks or geographic features
8. Any other location identifiers

Post from r/{subreddit}:
{full_text}

Return a JSON object with these fields:
- gmu_numbers: list of GMU/unit numbers mentioned
- counties: list of county names
- trails_peaks: list of trail/peak names
- towns_cities: list of town/city names
- coordinates: list of any GPS coordinates
- landmarks: list of other geographic features
- location_summary: brief summary of location info
- has_specific_location: boolean if post contains specific location data
"""
        
        try:
            # Use OpenAI directly
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a location data extractor. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            location_data = json.loads(result)
            location_data['post_title'] = post_title[:60] + "..."
            location_data['subreddit'] = subreddit
            location_data['species'] = sighting.get('species', 'unknown')
            location_analysis.append(location_data)
        except json.JSONDecodeError as e:
            console.print(f"[yellow]Error parsing JSON response: {e}[/yellow]")
            console.print(f"[yellow]Response was: {result}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Error analyzing post: {e}[/yellow]")
            continue
    
    # Display results
    console.print("\n[bold cyan]Location Data Analysis Results[/bold cyan]")
    console.print("=" * 80)
    
    # Summary statistics
    total_with_location = sum(1 for loc in location_analysis if loc.get('has_specific_location'))
    console.print(f"\n[bold]Posts with specific location data: {total_with_location}/{len(location_analysis)}[/bold]")
    
    # Location type frequency
    location_types = {
        'GMU Numbers': [],
        'Counties': [],
        'Trails/Peaks': [],
        'Towns/Cities': [],
        'Coordinates': [],
        'Landmarks': []
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
        if loc.get('coordinates'):
            location_types['Coordinates'].extend(loc['coordinates'])
        if loc.get('landmarks'):
            location_types['Landmarks'].extend(loc['landmarks'])
    
    # Display location type summary
    console.print("\n[bold]Location Types Found:[/bold]")
    table = Table()
    table.add_column("Location Type", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Examples", style="yellow")
    
    for loc_type, values in location_types.items():
        if values:
            unique_values = list(set(values))
            examples = ", ".join(unique_values[:3])
            if len(unique_values) > 3:
                examples += f" (+{len(unique_values)-3} more)"
            table.add_row(loc_type, str(len(values)), examples)
    
    console.print(table)
    
    # Show detailed examples
    console.print("\n[bold cyan]Sample Posts with Location Data:[/bold cyan]")
    console.print("-" * 80)
    
    posts_with_location = [loc for loc in location_analysis if loc.get('has_specific_location')][:5]
    
    for i, loc in enumerate(posts_with_location, 1):
        console.print(f"\n[bold green]Example {i}:[/bold green]")
        console.print(f"  [bold]Subreddit:[/bold] r/{loc['subreddit']}")
        console.print(f"  [bold]Species:[/bold] {loc['species']}")
        console.print(f"  [bold]Title:[/bold] {loc['post_title']}")
        console.print(f"  [bold]Location Summary:[/bold] {loc.get('location_summary', 'N/A')}")
        
        if loc.get('gmu_numbers'):
            console.print(f"  [bold]GMU Numbers:[/bold] {', '.join(loc['gmu_numbers'])}")
        if loc.get('counties'):
            console.print(f"  [bold]Counties:[/bold] {', '.join(loc['counties'])}")
        if loc.get('trails_peaks'):
            console.print(f"  [bold]Trails/Peaks:[/bold] {', '.join(loc['trails_peaks'])}")
        if loc.get('towns_cities'):
            console.print(f"  [bold]Towns/Cities:[/bold] {', '.join(loc['towns_cities'])}")
    
    # Save full analysis
    output_file = 'data/reddit_location_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(location_analysis, f, indent=2)
    
    console.print(f"\n[green]Full analysis saved to: {output_file}[/green]")

if __name__ == "__main__":
    analyze_location_content()
