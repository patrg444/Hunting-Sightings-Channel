#!/usr/bin/env python3
"""
Enhanced iNaturalist test showing GMU mapping and closest trail/peak.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.inaturalist_scraper import INaturalistScraper
from processors.gmu_processor import GMUProcessor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import json

console = Console()

def haversine_distance(lat1, lon1, lat2, lon2):
 """
 Calculate the great circle distance between two points
 on the earth (specified in decimal degrees).
 Returns distance in miles.
 """
 # Convert to radians
 lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

 # Haversine formula
 dlat = lat2 - lat1
 dlon = lon2 - lon1
 a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
 c = 2 * asin(sqrt(a))
 r = 3956 # Radius of earth in miles
 return c * r

def find_closest_trail(lat, lon, trails_df):
 """
 Find the closest trail or peak to given coordinates.
 Returns trail name, type, and distance in miles.
 """
 # Calculate distances to all trails/peaks
 distances = trails_df.apply(
 lambda row: haversine_distance(lat, lon, row['lat'], row['lon']),
 axis=1
 )

 # Find the closest one
 closest_idx = distances.idxmin()
 closest = trails_df.loc[closest_idx]

 return {
 'name': closest['name'],
 'type': closest['type'],
 'distance_miles': round(distances[closest_idx], 1),
 'gmu': closest['gmu']
 }

def test_inaturalist_with_trails():
 """Test iNaturalist with GMU mapping and closest trail/peak."""
 console.print("\n[bold cyan]iNaturalist + Trail/Peak Proximity Test[/bold cyan]")
 console.print("=" * 70)

 # Load components
 console.print("\n[yellow]Loading components...[/yellow]")

 # Initialize scrapers and processors
 scraper = INaturalistScraper()
 gmu_processor = GMUProcessor(gmu_data_path="data/gmu/colorado_gmu.geojson")
 gmu_processor.load_gmu_data()
 console.print(" GMU database loaded")

 # Load trail/peak index
 trails_df = pd.read_csv("data/trails/colorado_trails_index.csv")
 console.print(f" Trail index loaded ({len(trails_df)} trails and peaks)")

 # Get wildlife sightings
 console.print("\n[yellow]Fetching wildlife observations...[/yellow]")
 sightings = scraper.scrape(lookback_days=30)
 console.print(f" Found {len(sightings)} observations")

 # Process each sighting
 console.print("\n[yellow]Processing sightings with GMU and trail data...[/yellow]")
 enriched_sightings = []

 for sighting in sightings:
 # Copy original data
 enriched = sighting.copy()

 # Add GMU
 lat = sighting['location']['lat']
 lon = sighting['location']['lon']
 gmu_id = gmu_processor.find_gmu_for_point(lat, lon)
 enriched['gmu'] = gmu_id if gmu_id else 'Outside CO'

 # Find closest trail/peak
 closest = find_closest_trail(lat, lon, trails_df)
 enriched['closest_trail'] = closest

 enriched_sightings.append(enriched)

 # Display results in table
 console.print("\n[bold]Wildlife Sightings with Location Context:[/bold]")

 table = Table(title="iNaturalist Observations Enhanced", show_lines=True)
 table.add_column("Species", style="cyan", width=12)
 table.add_column("Date", style="yellow", width=10)
 table.add_column("Location", style="green", width=25)
 table.add_column("GMU", style="bold magenta", width=6)
 table.add_column("Closest Trail/Peak", style="blue", width=30)
 table.add_column("Distance", style="red", width=8)

 # Show first 15 sightings
 for sighting in enriched_sightings[:15]:
 location = sighting['location']['place_guess']
 if len(location) > 25:
 location = location[:22] + "..."

 closest = sighting['closest_trail']
 trail_info = f"{closest['name']} ({closest['type']})"
 if len(trail_info) > 30:
 trail_info = trail_info[:27] + "..."

 table.add_row(
 sighting['species'],
 sighting['observed_date'],
 location,
 str(sighting['gmu']),
 trail_info,
 f"{closest['distance_miles']} mi"
 )

 console.print(table)

 # Show some detailed examples
 console.print("\n[bold]Detailed Examples:[/bold]")
 for i, sighting in enumerate(enriched_sightings[:3]):
 console.print(f"\n[bold green]Example {i+1}:[/bold green]")

 info = f"""[bold]Species:[/bold] {sighting['species']}
[bold]Observed:[/bold] {sighting['observed_date']} at {sighting.get('observed_time', 'Unknown time')}
[bold]Location:[/bold] {sighting['location']['place_guess']}
[bold]Coordinates:[/bold] {sighting['location']['lat']:.4f}, {sighting['location']['lon']:.4f}
[bold]GMU:[/bold] {sighting['gmu']}
[bold]Closest Trail/Peak:[/bold] {sighting['closest_trail']['name']}
 • Type: {sighting['closest_trail']['type'].title()}
 • Distance: {sighting['closest_trail']['distance_miles']} miles
 • Trail GMU: {sighting['closest_trail']['gmu']}
[bold]Observer:[/bold] {sighting['observer']['username']}"""

 panel = Panel(info, border_style="dim")
 console.print(panel)

 # Save enriched data
 console.print("\n[yellow]Saving enriched data...[/yellow]")
 output_file = "data/sightings/inaturalist_with_trails.json"

 # Convert for JSON serialization
 save_data = []
 for s in enriched_sightings[:10]:
 save_item = s.copy()
 # Flatten the closest_trail data
 save_item['closest_trail_name'] = s['closest_trail']['name']
 save_item['closest_trail_type'] = s['closest_trail']['type']
 save_item['closest_trail_distance_miles'] = s['closest_trail']['distance_miles']
 save_item.pop('closest_trail', None)
 save_data.append(save_item)

 with open(output_file, 'w') as f:
 json.dump(save_data, f, indent=2, default=str)

 console.print(f" Saved enriched data to: {output_file}")

 # Summary statistics
 console.print("\n[bold cyan]Summary Statistics:[/bold cyan]")

 # Average distance to nearest trail
 avg_distance = np.mean([s['closest_trail']['distance_miles'] for s in enriched_sightings])
 console.print(f"• Average distance to nearest trail/peak: {avg_distance:.1f} miles")

 # Sightings within 1 mile of trail
 within_1_mile = sum(1 for s in enriched_sightings if s['closest_trail']['distance_miles'] <= 1.0)
 console.print(f"• Sightings within 1 mile of trail: {within_1_mile} ({within_1_mile/len(enriched_sightings)*100:.0f}%)")

 # Most common nearby trails
 trail_counts = {}
 for s in enriched_sightings:
 trail = s['closest_trail']['name']
 trail_counts[trail] = trail_counts.get(trail, 0) + 1

 console.print("\n[bold]Most Common Nearby Trails/Peaks:[/bold]")
 for trail, count in sorted(trail_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
 console.print(f" • {trail}: {count} sightings")

if __name__ == "__main__":
 test_inaturalist_with_trails()
