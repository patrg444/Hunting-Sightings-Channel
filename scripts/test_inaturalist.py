#!/usr/bin/env python3
"""
Test iNaturalist scraper to get structured wildlife sighting data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.inaturalist_scraper import INaturalistScraper
from processors.gmu_processor import GMUProcessor
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import json

console = Console()

def test_inaturalist_scraper():
    """Test the iNaturalist scraper for wildlife observations."""
    console.print("\n[bold cyan]Testing iNaturalist Wildlife Scraper[/bold cyan]")
    console.print("=" * 70)
    
    # Initialize scraper
    scraper = INaturalistScraper()
    
    # Initialize GMU processor to map coordinates to GMUs
    gmu_processor = GMUProcessor(gmu_data_path="data/gmu/colorado_gmu.geojson")
    try:
        gmu_processor.load_gmu_data()
        console.print("[green]GMU data loaded successfully[/green]")
    except Exception as e:
        console.print(f"[yellow]GMU data not available: {e}[/yellow]")
        gmu_processor = None
    
    console.print("\n[yellow]Fetching wildlife observations from last 7 days...[/yellow]")
    
    # Fetch recent observations (7 days for testing)
    sightings = scraper.scrape(lookback_days=7)
    
    if not sightings:
        console.print("[red]No observations found[/red]")
        return
    
    console.print(f"\n[green]Found {len(sightings)} wildlife observations![/green]")
    
    # Create summary table
    table = Table(title="Wildlife Sightings Summary")
    table.add_column("Species", style="cyan")
    table.add_column("Date", style="yellow")
    table.add_column("Time", style="yellow")
    table.add_column("Location", style="green")
    table.add_column("GMU", style="magenta")
    table.add_column("Observer", style="blue")
    
    # Process and display sightings
    for i, sighting in enumerate(sightings[:20]):  # Show first 20
        # Map to GMU
        gmu_str = "Unknown"
        if gmu_processor:
            gmu_id = gmu_processor.find_gmu_for_point(
                sighting['location']['lat'],
                sighting['location']['lon']
            )
            gmu_str = gmu_id if gmu_id else "Unknown"
        
        # Format location
        location = sighting['location']['place_guess'] or f"{sighting['location']['lat']:.4f}, {sighting['location']['lon']:.4f}"
        if len(location) > 30:
            location = location[:27] + "..."
        
        table.add_row(
            sighting['species'],
            sighting['observed_date'],
            sighting['observed_time'] or "N/A",
            location,
            gmu_str,
            sighting['observer']['username']
        )
    
    console.print(table)
    
    # Show detailed examples
    console.print("\n[bold]Detailed Examples (First 3 Sightings):[/bold]")
    console.print("-" * 70)
    
    for i, sighting in enumerate(sightings[:3]):
        # Map to GMU
        gmu_id = None
        if gmu_processor:
            gmu_id = gmu_processor.find_gmu_for_point(
                sighting['location']['lat'],
                sighting['location']['lon']
            )
        
        console.print(f"\n[bold green]Sighting {i+1}: {sighting['species']}[/bold green]")
        console.print(f"[bold]WHAT:[/bold] {sighting['species']}")
        console.print(f"[bold]WHERE:[/bold]")
        console.print(f"  • Coordinates: {sighting['location']['lat']:.6f}, {sighting['location']['lon']:.6f}")
        console.print(f"  • Place: {sighting['location']['place_guess']}")
        console.print(f"  • GMU: {gmu_id if gmu_id else 'Unknown'}")
        console.print(f"  • Accuracy: {sighting['location']['accuracy']}m" if sighting['location']['accuracy'] else "  • Accuracy: Unknown")
        console.print(f"[bold]WHEN:[/bold] {sighting['observed_date']}" + (f" at {sighting['observed_time']}" if sighting['observed_time'] else ""))
        console.print(f"[bold]WHO:[/bold] {sighting['observer']['name'] or sighting['observer']['username']}")
        if sighting['description']:
            console.print(f"[bold]NOTES:[/bold] {sighting['description'][:200]}...")
        if sighting['photo_url']:
            console.print(f"[bold]PHOTO:[/bold] {sighting['photo_url']}")
        console.print(f"[bold]iNaturalist:[/bold] {sighting['inaturalist_url']}")
        console.print(f"[bold]Quality:[/bold] {sighting['quality_grade']} (confidence: {sighting['confidence']})")
    
    # Species distribution
    console.print("\n[bold cyan]Species Distribution:[/bold cyan]")
    species_counts = {}
    for sighting in sightings:
        species = sighting['species']
        species_counts[species] = species_counts.get(species, 0) + 1
    
    species_table = Table()
    species_table.add_column("Species", style="cyan")
    species_table.add_column("Count", style="yellow")
    species_table.add_column("Percentage", style="green")
    
    total = len(sightings)
    for species, count in sorted(species_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        species_table.add_row(species, str(count), f"{percentage:.1f}%")
    
    console.print(species_table)
    
    # Save sample data
    sample_file = "data/sightings/inaturalist_sample.json"
    os.makedirs(os.path.dirname(sample_file), exist_ok=True)
    with open(sample_file, 'w') as f:
        json.dump(sightings[:10], f, indent=2, default=str)
    console.print(f"\n[green]Sample data saved to: {sample_file}[/green]")

if __name__ == "__main__":
    test_inaturalist_scraper()
