#!/usr/bin/env python3
"""
Test real web scraping for 14ers.com with authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.fourteeners_auth_scraper import FourteenersAuthScraper
from rich.console import Console
from rich.table import Table

console = Console()

def test_auth_14ers():
    """Test authenticated 14ers.com scraping."""
    console.print("[bold green]Testing Authenticated 14ers.com Scraping...[/bold green]\n")
    
    # Create scraper instance
    scraper = FourteenersAuthScraper()
    
    # Try to scrape with 7 day lookback
    console.print("Attempting to login and scrape recent trip reports (7 day lookback)...")
    
    try:
        sightings = scraper.scrape(lookback_days=7)
        
        if sightings:
            console.print(f"\n✅ Found {len(sightings)} wildlife sightings!")
            
            # Show results in a table
            table = Table(title="Real Wildlife Sightings from 14ers.com")
            table.add_column("Date", style="cyan")
            table.add_column("Species", style="green")
            table.add_column("Trail/Peak", style="blue", max_width=30)
            table.add_column("Context", style="white", max_width=40)
            
            for sighting in sightings[:10]:  # Show first 10
                date_str = sighting['sighting_date'].strftime('%m/%d/%Y')
                species = sighting['species'].replace('_', ' ').title()
                trail = sighting.get('trail_name', 'Unknown')[:30]
                context = sighting['raw_text'][:40] + "..."
                
                table.add_row(date_str, species, trail, context)
            
            console.print(table)
            
            # Summary
            console.print("\n[bold]Summary by Species:[/bold]")
            species_counts = {}
            for s in sightings:
                species = s['species'].replace('_', ' ').title()
                species_counts[species] = species_counts.get(species, 0) + 1
            
            for species, count in sorted(species_counts.items()):
                console.print(f"  • {species}: {count}")
            
            # Show some URLs
            console.print("\n[bold]Sample Report URLs:[/bold]")
            unique_urls = list(set(s['source_url'] for s in sightings))
            for url in unique_urls[:3]:
                console.print(f"  • {url}")
                
        else:
            console.print("\n⚠️  No wildlife sightings found in recent reports")
            console.print("This could mean:")
            console.print("  - No recent trip reports mention wildlife")
            console.print("  - The login failed")
            console.print("  - The parsing needs adjustment")
            
    except Exception as e:
        console.print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth_14ers()
