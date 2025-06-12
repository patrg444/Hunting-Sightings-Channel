#!/usr/bin/env python3
"""
Build a complete trail and peak index for Colorado with GMU mappings.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.osm_scraper import OSMScraper
from processors.gmu_processor import GMUProcessor
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import track
import pandas as pd
import json

console = Console()

def build_trail_index():
 """Build comprehensive trail index with GMU mappings."""
 console.print("\n[bold cyan]Building Colorado Trail & Peak Index[/bold cyan]")
 console.print("=" * 70)

 # Step 1: Initialize components
 console.print("\n[yellow]Step 1: Initializing components...[/yellow]")
 osm_scraper = OSMScraper()
 gmu_processor = GMUProcessor(gmu_data_path="data/gmu/colorado_gmu.geojson")
 gmu_processor.load_gmu_data()
 console.print(" OSM scraper initialized")
 console.print(" GMU processor loaded (185 GMUs)")

 # Step 2: Fetch OSM data
 console.print("\n[yellow]Step 2: Fetching trail and peak data from OpenStreetMap...[/yellow]")
 trails_peaks = osm_scraper.scrape(use_cache=True)
 console.print(f" Found {len(trails_peaks)} trails and peaks")

 # Step 3: Map to GMUs
 console.print("\n[yellow]Step 3: Mapping trails/peaks to GMUs...[/yellow]")

 # Add GMU column
 for item in track(trails_peaks, description="Mapping to GMUs"):
 gmu = gmu_processor.find_gmu_for_point(item['lat'], item['lon'])
 item['gmu'] = gmu if gmu else 'Unknown'

 # Step 4: Save results
 console.print("\n[yellow]Step 4: Saving results...[/yellow]")

 # Save full dataset with GMU mappings
 df = pd.DataFrame(trails_peaks)
 output_path = "data/trails/colorado_trails_peaks_with_gmu.csv"
 df.to_csv(output_path, index=False)
 console.print(f" Saved full dataset to {output_path}")

 # Also save simplified version (name, lat, lon, gmu)
 simple_df = df[['name', 'lat', 'lon', 'gmu', 'type', 'elevation']]
 simple_path = "data/trails/colorado_trails_index.csv"
 simple_df.to_csv(simple_path, index=False)
 console.print(f" Saved simplified index to {simple_path}")

 # Step 5: Show statistics
 console.print("\n[bold cyan]Summary Statistics:[/bold cyan]")

 # Type breakdown
 type_counts = df['type'].value_counts()
 type_table = Table(title="Features by Type")
 type_table.add_column("Type", style="cyan")
 type_table.add_column("Count", style="yellow")
 for feat_type, count in type_counts.items():
 type_table.add_row(feat_type.title(), str(count))
 console.print(type_table)

 # GMU coverage
 gmu_counts = df['gmu'].value_counts()
 console.print(f"\n[green]GMU Coverage:[/green]")
 console.print(f" • Features mapped to GMUs: {len(df[df['gmu'] != 'Unknown'])}")
 console.print(f" • Features outside GMUs: {len(df[df['gmu'] == 'Unknown'])}")
 console.print(f" • Unique GMUs with features: {len(gmu_counts) - (1 if 'Unknown' in gmu_counts else 0)}")

 # Show sample results
 console.print("\n[bold]Sample Results:[/bold]")
 sample_table = Table()
 sample_table.add_column("Name", style="cyan")
 sample_table.add_column("Type", style="yellow")
 sample_table.add_column("GMU", style="magenta")
 sample_table.add_column("Elevation", style="green")

 # Show some peaks
 peaks = df[df['type'] == 'peak'].head(5)
 for _, peak in peaks.iterrows():
 sample_table.add_row(
 peak['name'],
 "Peak",
 str(peak['gmu']),
 f"{peak['elevation']}m" if pd.notna(peak['elevation']) else "N/A"
 )

 # Show some trails
 trails = df[df['type'] == 'trail'].head(5)
 for _, trail in trails.iterrows():
 sample_table.add_row(
 trail['name'],
 "Trail",
 str(trail['gmu']),
 f"{trail['elevation']}m" if pd.notna(trail['elevation']) else "N/A"
 )

 console.print(sample_table)

 return df

def lookup_demo():
 """Demonstrate trail/peak to GMU lookup."""
 console.print("\n[bold cyan]Trail/Peak Lookup Demo[/bold cyan]")
 console.print("=" * 70)

 # Load the index
 df = pd.read_csv("data/trails/colorado_trails_index.csv")

 # Example lookups
 examples = [
 "Lost Creek Trail",
 "Mount Elbert",
 "Grays Peak",
 "Bear Lake Trail"
 ]

 for name in examples:
 # Case-insensitive partial match
 matches = df[df['name'].str.contains(name, case=False, na=False)]

 if not matches.empty:
 match = matches.iloc[0]
 console.print(f"\n[green]'{name}' → GMU {match['gmu']}[/green]")
 console.print(f" • Full name: {match['name']}")
 console.print(f" • Type: {match['type']}")
 console.print(f" • Coordinates: {match['lat']:.4f}, {match['lon']:.4f}")
 if pd.notna(match['elevation']):
 console.print(f" • Elevation: {match['elevation']}m")
 else:
 console.print(f"\n[red]'{name}' not found in index[/red]")

if __name__ == "__main__":
 import argparse

 parser = argparse.ArgumentParser(description="Build trail index with GMU mappings")
 parser.add_argument("--demo", action="store_true", help="Run lookup demo")
 args = parser.parse_args()

 if args.demo:
 lookup_demo()
 else:
 build_trail_index()
 console.print("\n[green]Trail index built successfully![/green]")
 console.print("Run with --demo flag to see lookup examples")
