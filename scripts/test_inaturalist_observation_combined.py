#!/usr/bin/env python3
"""
Test combined wildlife data from iNaturalist and Observation.org with GMU and trail mapping.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.inaturalist_scraper import INaturalistScraper
from scrapers.observation_org_scraper import ObservationOrgScraper
from processors.gmu_processor import GMUProcessor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from collections import Counter
import json

console = Console()

def haversine_distance(lat1, lon1, lat2, lon2):
 """Calculate distance between two points in miles."""
 lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
 dlat = lat2 - lat1
 dlon = lon2 - lon1
 a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
 c = 2 * asin(sqrt(a))
 r = 3956 # Radius of earth in miles
 return c * r

def find_closest_trail(lat, lon, trails_df):
 """Find the closest trail or peak to given coordinates."""
 distances = trails_df.apply(
 lambda row: haversine_distance(lat, lon, row['lat'], row['lon']),
 axis=1
 )
 closest_idx = distances.idxmin()
 closest = trails_df.loc[closest_idx]

 return {
 'name': closest['name'],
 'type': closest['type'],
 'distance_miles': round(distances[closest_idx], 1),
 'gmu': closest['gmu']
 }

def test_combined_sources():
 """Test iNaturalist and Observation.org data together."""
 console.print("\n[bold cyan]Combined Wildlife Data: iNaturalist + Observation.org[/bold cyan]")
 console.print("=" * 70)

 # Load components
 console.print("\n[yellow]Loading components...[/yellow]")

 # Initialize processors
 gmu_processor = GMUProcessor(gmu_data_path="data/gmu/colorado_gmu.geojson")
 gmu_processor.load_gmu_data()
 console.print(" GMU database loaded (185 Colorado GMUs)")

 # Load trail/peak index
 trails_df = pd.read_csv("data/trails/colorado_trails_index.csv")
 console.print(f" Trail index loaded ({len(trails_df)} trails and peaks)")

 # Initialize scrapers
 scrapers = {
 'iNaturalist': INaturalistScraper(),
 'Observation.org': ObservationOrgScraper()
 }

 all_sightings = []
 source_counts = {}

 # Fetch from each source
 console.print("\n[yellow]Fetching wildlife observations...[/yellow]")

 for source_name, scraper in scrapers.items():
 console.print(f"\n[cyan]Fetching from {source_name}...[/cyan]")
 try:
 # Use 30 days for more data
 sightings = scraper.scrape(lookback_days=30)
 console.print(f" Found {len(sightings)} observations")

 # Enrich each sighting with GMU and trail data
 for sighting in track(sightings, description=f"Processing {source_name}"):
 # Add source name
 sighting['source'] = source_name

 # Add GMU
 lat = sighting['location']['lat']
 lon = sighting['location']['lon']
 gmu_id = gmu_processor.find_gmu_for_point(lat, lon)
 sighting['gmu'] = gmu_id if gmu_id else 'Outside CO'

 # Find closest trail/peak
 closest = find_closest_trail(lat, lon, trails_df)
 sighting['closest_trail'] = closest

 all_sightings.append(sighting)

 source_counts[source_name] = len(sightings)

 except Exception as e:
 console.print(f" Error: {e}")
 source_counts[source_name] = 0

 console.print(f"\n[green]Total observations collected: {len(all_sightings)}[/green]")

 # Display source summary
 console.print("\n[bold]Data Source Summary:[/bold]")
 source_table = Table()
 source_table.add_column("Source", style="cyan")
 source_table.add_column("Observations", style="yellow")
 source_table.add_column("Coverage", style="green")

 for source, count in source_counts.items():
 if source == 'iNaturalist':
 coverage = "All species (photo-verified)"
 else:
 coverage = "Mammals + other wildlife"
 source_table.add_row(source, str(count), coverage)

 console.print(source_table)

 if not all_sightings:
 console.print("\n[red]No sightings found from any source[/red]")
 return

 # Sort by date (most recent first)
 all_sightings.sort(key=lambda x: x['observed_date'], reverse=True)

 # Display combined results
 console.print("\n[bold]Recent Wildlife Sightings:[/bold]")

 table = Table(title="Combined Wildlife Observations", show_lines=True)
 table.add_column("Species", style="cyan", width=15)
 table.add_column("Date", style="yellow", width=10)
 table.add_column("Time", style="yellow", width=5)
 table.add_column("GMU", style="bold magenta", width=5)
 table.add_column("Closest Trail/Peak", style="blue", width=25)
 table.add_column("Dist", style="red", width=6)
 table.add_column("Source", style="green", width=13)

 # Show first 20 sightings
 for sighting in all_sightings[:20]:
 closest = sighting['closest_trail']
 trail_info = f"{closest['name']} ({closest['type']})"
 if len(trail_info) > 25:
 trail_info = trail_info[:22] + "..."

 time_str = sighting.get('observed_time', 'N/A')
 if time_str and time_str != 'N/A':
 time_str = time_str[:5] # Just HH:MM

 table.add_row(
 sighting['species'],
 sighting['observed_date'],
 time_str,
 str(sighting['gmu']),
 trail_info,
 f"{closest['distance_miles']}mi",
 sighting['source']
 )

 console.print(table)

 # Species diversity analysis
 console.print("\n[bold cyan]Species Diversity:[/bold cyan]")
 species_counter = Counter([s['species'] for s in all_sightings])

 species_table = Table()
 species_table.add_column("Species", style="cyan")
 species_table.add_column("Count", style="yellow")
 species_table.add_column("Sources", style="green")

 for species, count in species_counter.most_common(15):
 # Find which sources reported this species
 sources = set([s['source'] for s in all_sightings if s['species'] == species])
 sources_str = " + ".join(sorted(sources))
 species_table.add_row(species, str(count), sources_str)

 console.print(species_table)

 # GMU activity analysis
 console.print("\n[bold cyan]Top GMUs by Activity:[/bold cyan]")
 gmu_counter = Counter([s['gmu'] for s in all_sightings if s['gmu'] != 'Outside CO'])

 if gmu_counter:
 hotspot_table = Table()
 hotspot_table.add_column("GMU", style="magenta")
 hotspot_table.add_column("Sightings", style="yellow")
 hotspot_table.add_column("Top Species", style="cyan")

 for gmu, count in gmu_counter.most_common(10):
 # Find top species in this GMU
 gmu_sightings = [s for s in all_sightings if s['gmu'] == gmu]
 gmu_species = Counter([s['species'] for s in gmu_sightings])
 top_species = ", ".join([f"{sp} ({ct})" for sp, ct in gmu_species.most_common(3)])
 if len(top_species) > 40:
 top_species = top_species[:37] + "..."
 hotspot_table.add_row(str(gmu), str(count), top_species)

 console.print(hotspot_table)

 # Trail proximity stats
 distances = [s['closest_trail']['distance_miles'] for s in all_sightings]
 if distances:
 avg_distance = np.mean(distances)
 within_1_mile = sum(1 for d in distances if d <= 1.0)

 console.print("\n[bold cyan]Trail Proximity:[/bold cyan]")
 console.print(f"• Average distance to trail: {avg_distance:.1f} miles")
 console.print(f"• Within 1 mile of trail: {within_1_mile} ({within_1_mile/len(all_sightings)*100:.0f}%)")

 # Save combined data
 console.print("\n[yellow]Saving combined data...[/yellow]")
 output_file = "data/sightings/combined_wildlife.json"

 # Prepare data for JSON (limit to 50 for file size)
 save_data = []
 for s in all_sightings[:50]:
 save_item = s.copy()
 # Flatten nested data
 save_item['closest_trail_name'] = s['closest_trail']['name']
 save_item['closest_trail_distance'] = s['closest_trail']['distance_miles']
 save_item.pop('closest_trail', None)
 save_data.append(save_item)

 with open(output_file, 'w') as f:
 json.dump(save_data, f, indent=2, default=str)

 console.print(f" Saved to: {output_file}")

 # Final summary
 console.print("\n[bold green]Summary:[/bold green]")
 console.print(f"• Total observations: {len(all_sightings)}")
 console.print(f"• Unique species: {len(species_counter)}")
 console.print(f"• Date range: {all_sightings[-1]['observed_date'] if all_sightings else 'N/A'} to {all_sightings[0]['observed_date'] if all_sightings else 'N/A'}")
 console.print(f"• Sources: iNaturalist (verified photos) + Observation.org (broad coverage)")

if __name__ == "__main__":
 test_combined_sources()
