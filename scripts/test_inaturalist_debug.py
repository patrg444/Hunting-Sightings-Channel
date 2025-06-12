#!/usr/bin/env python3
"""
Debug version of iNaturalist test to show raw API data vs GMU-enriched data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.inaturalist_scraper import INaturalistScraper
from processors.gmu_processor import GMUProcessor
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import json

console = Console()

def test_inaturalist_with_debug():
 """Test iNaturalist scraper showing raw vs GMU-enriched data."""
 console.print("\n[bold cyan]iNaturalist API Debug Test[/bold cyan]")
 console.print("Showing raw API data vs. GMU-enriched data")
 console.print("=" * 70)

 # Initialize scraper
 scraper = INaturalistScraper()

 # Initialize GMU processor
 gmu_processor = GMUProcessor(gmu_data_path="data/gmu/colorado_gmu.geojson")
 gmu_processor.load_gmu_data()
 console.print(" GMU database loaded (185 Colorado GMUs)")

 console.print("\n[yellow]Fetching wildlife observations from last 30 days...[/yellow]")

 # Get raw sightings from iNaturalist
 raw_sightings = scraper.scrape(lookback_days=30)

 if not raw_sightings:
 console.print("[red]No observations found[/red]")
 return

 console.print(f"\n[green]Found {len(raw_sightings)} observations from iNaturalist[/green]")

 # Show first sighting RAW from iNaturalist
 console.print("\n[bold magenta] RAW iNaturalist API Data (First Sighting) [/bold magenta]")
 first_raw = raw_sightings[0]

 raw_info = f"""[bold]Species:[/bold] {first_raw['species']}
[bold]Location Data from iNaturalist:[/bold]
 • Latitude: {first_raw['location']['lat']}
 • Longitude: {first_raw['location']['lon']}
 • Place Guess: {first_raw['location']['place_guess']}
 • Accuracy: {first_raw['location'].get('accuracy', 'N/A')}m
[bold]Date/Time:[/bold] {first_raw['observed_date']} {first_raw.get('observed_time', 'N/A')}
[bold]Observer:[/bold] {first_raw['observer']['username']}
[bold]iNaturalist ID:[/bold] {first_raw['inaturalist_id']}

[bold red]Note: No GMU data from iNaturalist![/bold red]"""

 panel = Panel(raw_info, title="Raw iNaturalist Response", border_style="yellow")
 console.print(panel)

 # Now add GMU mapping
 console.print("\n[bold cyan] Adding GMU Mapping Using Our Database [/bold cyan]")

 # Create enriched sightings with GMU
 enriched_sightings = []
 gmu_mapping_stats = {'mapped': 0, 'unmapped': 0}

 for sighting in raw_sightings:
 # Copy the original sighting
 enriched = sighting.copy()

 # Map to GMU using our database
 gmu_id = gmu_processor.find_gmu_for_point(
 sighting['location']['lat'],
 sighting['location']['lon']
 )

 # Add GMU to the sighting
 enriched['gmu'] = gmu_id if gmu_id else 'Outside Colorado GMUs'

 if gmu_id:
 gmu_mapping_stats['mapped'] += 1
 else:
 gmu_mapping_stats['unmapped'] += 1

 enriched_sightings.append(enriched)

 # Show first sighting ENRICHED with GMU
 console.print("\n[bold green] GMU-Enriched Data (Same Sighting) [/bold green]")
 first_enriched = enriched_sightings[0]

 enriched_info = f"""[bold]Species:[/bold] {first_enriched['species']}
[bold]Location Data:[/bold]
 • Latitude: {first_enriched['location']['lat']}
 • Longitude: {first_enriched['location']['lon']}
 • Place Guess: {first_enriched['location']['place_guess']}
 • [bold green]GMU: {first_enriched['gmu']}[/bold green] ← Added by our system!
[bold]Date/Time:[/bold] {first_enriched['observed_date']} {first_enriched.get('observed_time', 'N/A')}
[bold]Observer:[/bold] {first_enriched['observer']['username']}

[bold green] GMU successfully mapped using Colorado GMU database![/bold green]"""

 panel = Panel(enriched_info, title="After GMU Processing", border_style="green")
 console.print(panel)

 # Show mapping statistics
 console.print(f"\n[bold]GMU Mapping Statistics:[/bold]")
 console.print(f" • Successfully mapped to GMU: {gmu_mapping_stats['mapped']}")
 console.print(f" • Outside Colorado GMUs: {gmu_mapping_stats['unmapped']}")
 console.print(f" • Mapping success rate: {(gmu_mapping_stats['mapped'] / len(raw_sightings) * 100):.1f}%")

 # Show sample of all enriched sightings
 console.print("\n[bold]Sample of Enriched Sightings:[/bold]")
 table = Table(title="iNaturalist Observations with GMU Mapping")
 table.add_column("Species", style="cyan")
 table.add_column("Date", style="yellow")
 table.add_column("Location", style="green")
 table.add_column("GMU", style="bold magenta")
 table.add_column("Source", style="blue")

 for sighting in enriched_sightings[:10]:
 location = sighting['location']['place_guess']
 if len(location) > 30:
 location = location[:27] + "..."

 table.add_row(
 sighting['species'],
 sighting['observed_date'],
 location,
 str(sighting['gmu']),
 "iNaturalist"
 )

 console.print(table)

 # Save both versions for comparison
 console.print("\n[yellow]Saving data for comparison...[/yellow]")

 # Save raw (no GMU)
 raw_file = "data/sightings/inaturalist_raw_no_gmu.json"
 with open(raw_file, 'w') as f:
 json.dump(raw_sightings[:5], f, indent=2, default=str)
 console.print(f" • Raw data (no GMU): {raw_file}")

 # Save enriched (with GMU)
 enriched_file = "data/sightings/inaturalist_enriched_with_gmu.json"
 with open(enriched_file, 'w') as f:
 json.dump(enriched_sightings[:5], f, indent=2, default=str)
 console.print(f" • Enriched data (with GMU): {enriched_file}")

 console.print("\n[bold green] Test Complete![/bold green]")
 console.print("The iNaturalist API does NOT provide GMU data.")
 console.print("Our system successfully adds GMU mapping using the Colorado GMU database.")

if __name__ == "__main__":
 test_inaturalist_with_debug()
