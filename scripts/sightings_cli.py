#!/usr/bin/env python3
"""
CLI tool for running scrapers and querying wildlife sightings.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from scrapers import FourteenersScraper, SummitPostScraper, RedditScraper
from processors import GMUProcessor, TrailProcessor


console = Console()


def map_sighting_to_gmu(sighting: Dict[str, Any], trail_processor: TrailProcessor, 
                       gmu_processor: GMUProcessor) -> Optional[str]:
    """
    Map a sighting to its GMU based on trail location.
    
    Args:
        sighting: Sighting dictionary
        trail_processor: Trail processor instance
        gmu_processor: GMU processor instance
        
    Returns:
        GMU ID or None if not mappable
    """
    # Try to find trail in our index
    trail_name = sighting.get('trail_name')
    if trail_name:
        trail = trail_processor.find_trail_by_name(trail_name)
        if trail and 'lat' in trail and 'lon' in trail:
            gmu = gmu_processor.find_gmu_for_point(trail['lat'], trail['lon'])
            return gmu
    
    # If we have direct coordinates (future enhancement)
    if 'lat' in sighting and 'lon' in sighting:
        return gmu_processor.find_gmu_for_point(sighting['lat'], sighting['lon'])
    
    return None


def run_scrapers(lookback_days: int = 1) -> List[Dict[str, Any]]:
    """
    Run all enabled scrapers and collect sightings.
    
    Args:
        lookback_days: Days to look back for content
        
    Returns:
        Combined list of all sightings
    """
    all_sightings = []
    
    scrapers = [
        ('14ers.com', FourteenersScraper),
        ('SummitPost', SummitPostScraper),
        ('Reddit', RedditScraper)
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for name, scraper_class in scrapers:
            task = progress.add_task(f"Scraping {name}...", total=None)
            
            try:
                scraper = scraper_class()
                sightings = scraper.scrape(lookback_days)
                all_sightings.extend(sightings)
                
                progress.update(task, description=f"✓ {name}: {len(sightings)} sightings")
            except Exception as e:
                logger.error(f"Error scraping {name}: {e}")
                progress.update(task, description=f"✗ {name}: Error")
            
            progress.remove_task(task)
    
    return all_sightings


def filter_sightings(sightings: List[Dict[str, Any]], 
                    date: Optional[str] = None,
                    units: Optional[List[str]] = None,
                    species: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Filter sightings based on criteria.
    
    Args:
        sightings: List of all sightings
        date: Date string ('yesterday', 'today', or YYYY-MM-DD)
        units: List of GMU IDs to filter by
        species: Species to filter by
        
    Returns:
        Filtered list of sightings
    """
    filtered = sightings
    
    # Filter by date
    if date:
        if date == 'yesterday':
            target_date = datetime.now().date() - timedelta(days=1)
        elif date == 'today':
            target_date = datetime.now().date()
        else:
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]Invalid date format: {date}[/red]")
                return []
        
        filtered = [s for s in filtered 
                   if s.get('sighting_date') and s['sighting_date'].date() == target_date]
    
    # Filter by GMU
    if units:
        filtered = [s for s in filtered if s.get('gmu_unit') in units]
    
    # Filter by species
    if species:
        filtered = [s for s in filtered if s.get('species') == species]
    
    return filtered


def display_sightings(sightings: List[Dict[str, Any]]):
    """
    Display sightings in a formatted table.
    
    Args:
        sightings: List of sightings to display
    """
    if not sightings:
        console.print("[yellow]No sightings found matching your criteria.[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Wildlife Sightings ({len(sightings)} found)")
    table.add_column("Date", style="cyan")
    table.add_column("Species", style="green")
    table.add_column("GMU", style="yellow")
    table.add_column("Location", style="blue")
    table.add_column("Context", style="white", max_width=50)
    table.add_column("Source", style="magenta")
    
    # Add rows
    for sighting in sightings:
        date_str = sighting['sighting_date'].strftime('%Y-%m-%d')
        species = sighting['species'].replace('_', ' ').title()
        gmu = sighting.get('gmu_unit', 'Unknown')
        location = sighting.get('trail_name', 'Unknown')
        context = sighting['raw_text'][:50] + '...' if len(sighting['raw_text']) > 50 else sighting['raw_text']
        source = sighting['source_type']
        
        table.add_row(date_str, species, gmu, location, context, source)
    
    console.print(table)
    
    # Summary by species
    console.print("\n[bold]Summary by Species:[/bold]")
    species_counts = {}
    for s in sightings:
        species = s['species'].replace('_', ' ').title()
        species_counts[species] = species_counts.get(species, 0) + 1
    
    for species, count in sorted(species_counts.items()):
        console.print(f"  • {species}: {count}")


@click.command()
@click.option('--date', default=None, 
              help='Date to filter by (yesterday, today, or YYYY-MM-DD)')
@click.option('--units', default=None, 
              help='Comma-separated GMU units to filter by (e.g., 12,201)')
@click.option('--species', default=None,
              type=click.Choice(['elk', 'deer', 'bear', 'pronghorn', 'bighorn_sheep', 'mountain_goat']),
              help='Species to filter by')
@click.option('--lookback', default=1, type=int,
              help='Days to look back when scraping (default: 1)')
@click.option('--no-scrape', is_flag=True,
              help='Skip scraping and use cached data')
def main(date, units, species, lookback, no_scrape):
    """
    Hunt Sightings CLI - Query wildlife sightings by date, GMU, and species.
    
    Examples:
        python sightings_cli.py --date yesterday --units 12,201 --species elk
        python sightings_cli.py --date 2025-06-03 --species bear
        python sightings_cli.py --lookback 7
    """
    console.print("[bold green]🦌 Hunting Sightings Channel CLI[/bold green]\n")
    
    # Load processors
    console.print("Loading GMU and trail data...")
    gmu_processor = GMUProcessor("data/gmu/colorado_gmu_sample.geojson")
    try:
        gmu_processor.load_gmu_data()
    except FileNotFoundError:
        console.print("[red]GMU data not found. Run setup_milestone1.py first.[/red]")
        return
    
    trail_processor = TrailProcessor()
    trail_processor.load_trail_index()
    
    # Run scrapers or load cached data
    if no_scrape:
        console.print("[yellow]Using cached data (--no-scrape specified)[/yellow]")
        # In a real implementation, we'd load from database
        sightings = []
    else:
        console.print(f"Scraping sources (looking back {lookback} days)...\n")
        sightings = run_scrapers(lookback)
        
        # Map sightings to GMUs
        console.print("\nMapping sightings to GMUs...")
        for sighting in sightings:
            sighting['gmu_unit'] = map_sighting_to_gmu(sighting, trail_processor, gmu_processor)
    
    # Parse units parameter
    unit_list = None
    if units:
        unit_list = [u.strip() for u in units.split(',')]
    
    # Filter sightings
    filtered_sightings = filter_sightings(sightings, date, unit_list, species)
    
    # Display results
    console.print()
    display_sightings(filtered_sightings)
    
    # Show source URLs
    if filtered_sightings:
        console.print("\n[bold]View full reports:[/bold]")
        unique_urls = set(s['source_url'] for s in filtered_sightings)
        for url in list(unique_urls)[:5]:  # Show max 5 URLs
            console.print(f"  • {url}")


if __name__ == "__main__":
    main()
