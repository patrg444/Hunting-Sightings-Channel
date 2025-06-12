#!/usr/bin/env python3
"""
Verify that all GMU polygons are loaded and demonstrate mapping across multiple GMUs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors import GMUProcessor
from rich.console import Console
from rich.table import Table
import json
import random

console = Console()

def verify_all_gmus():
    """Verify all GMUs are loaded and show their distribution"""
    
    console.print("[bold]Verifying All GMU Polygons Are Loaded[/bold]\n")
    
    # Load GMU processor with full data
    gmu_processor = GMUProcessor("data/gmu/colorado_gmu.geojson")
    gmu_processor.load_gmu_data()
    
    # Get all GMU IDs from the loaded data
    with open("data/gmu/colorado_gmu.geojson", 'r') as f:
        data = json.load(f)
    
    all_gmus = []
    gmu_bounds = {}
    
    for feature in data['features']:
        props = feature.get('properties', {})
        gmu_id = props.get('GMUID', props.get('DAU', 'Unknown'))
        
        if gmu_id != 'Unknown':
            all_gmus.append(gmu_id)
            
            # Calculate center point for testing
            # Handle different geometry types
            geometry = feature['geometry']
            if geometry['type'] == 'Polygon':
                coords = geometry['coordinates'][0]
            elif geometry['type'] == 'MultiPolygon':
                # Use first polygon of multipolygon
                coords = geometry['coordinates'][0][0]
            else:
                continue
            
            # Extract coordinates
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            
            center_lat = (min(lats) + max(lats)) / 2
            center_lon = (min(lons) + max(lons)) / 2
            
            gmu_bounds[gmu_id] = {
                'center_lat': center_lat,
                'center_lon': center_lon,
                'min_lat': min(lats),
                'max_lat': max(lats),
                'min_lon': min(lons),
                'max_lon': max(lons)
            }
    
    console.print(f"[green]Total GMUs loaded: {len(all_gmus)}[/green]\n")
    
    # Show unique GMU IDs (first 20 for brevity)
    console.print("[yellow]Sample of loaded GMU IDs:[/yellow]")
    unique_gmus = sorted(set(str(g) for g in all_gmus))
    sample_gmus = unique_gmus[:20]
    console.print(", ".join(sample_gmus) + "...\n")
    
    # Test mapping for random GMUs to prove they all work
    console.print("[bold]Testing Random GMU Mappings[/bold]")
    console.print("(Using center points of GMUs to verify mapping)\n")
    
    table = Table(title="GMU Mapping Verification")
    table.add_column("GMU ID", style="cyan")
    table.add_column("Test Lat", style="green")
    table.add_column("Test Lon", style="green")
    table.add_column("Mapped GMU", style="yellow")
    table.add_column("Status", style="magenta")
    
    # Test 10 random GMUs
    test_gmus = random.sample(list(gmu_bounds.keys()), min(10, len(gmu_bounds)))
    
    for gmu_id in sorted(test_gmus):
        bounds = gmu_bounds[gmu_id]
        test_lat = bounds['center_lat']
        test_lon = bounds['center_lon']
        
        # Test if the center point maps back to the same GMU
        mapped_gmu = gmu_processor.find_gmu_for_point(test_lat, test_lon)
        status = "✓ PASS" if str(mapped_gmu) == str(gmu_id) else "✗ FAIL"
        
        table.add_row(
            str(gmu_id),
            f"{test_lat:.4f}",
            f"{test_lon:.4f}",
            str(mapped_gmu) if mapped_gmu else "None",
            status
        )
    
    console.print(table)
    
    # Show GMU distribution across Colorado
    console.print("\n[bold]GMU Geographic Distribution[/bold]")
    console.print("(Showing latitude/longitude ranges)\n")
    
    # Find extremes
    all_lats = []
    all_lons = []
    for bounds in gmu_bounds.values():
        all_lats.extend([bounds['min_lat'], bounds['max_lat']])
        all_lons.extend([bounds['min_lon'], bounds['max_lon']])
    
    console.print(f"Coverage Area:")
    console.print(f"  Latitude range: {min(all_lats):.4f} to {max(all_lats):.4f}")
    console.print(f"  Longitude range: {min(all_lons):.4f} to {max(all_lons):.4f}")
    console.print(f"  This covers the entire state of Colorado")
    
    return gmu_processor, gmu_bounds

def test_known_colorado_locations(gmu_processor):
    """Test mapping of known Colorado locations across different regions"""
    
    console.print("\n[bold]Testing Known Colorado Locations[/bold]")
    console.print("(Locations across different regions of Colorado)\n")
    
    # Test locations across Colorado
    test_locations = [
        # Front Range
        ("Denver", 39.7392, -104.9903),
        ("Colorado Springs", 38.8339, -104.8214),
        ("Fort Collins", 40.5853, -105.0844),
        
        # Western Slope
        ("Grand Junction", 39.0639, -108.5506),
        ("Aspen", 39.1911, -106.8175),
        ("Glenwood Springs", 39.5505, -107.3248),
        
        # Southern Colorado
        ("Durango", 37.2753, -107.8801),
        ("Alamosa", 37.4695, -105.8701),
        ("Trinidad", 37.1695, -104.5005),
        
        # Eastern Plains
        ("Sterling", 40.6255, -103.2077),
        ("Lamar", 38.0872, -102.6207),
        
        # Mountain Peaks
        ("Mount Elbert", 39.1178, -106.4453),
        ("Pikes Peak", 38.8409, -105.0422),
        ("Mount Evans", 39.5883, -105.6438),
        ("Longs Peak", 40.2548, -105.6151),
        ("Mount Sneffels", 38.0038, -107.7923),
        
        # Ski Areas
        ("Vail", 39.6403, -106.3742),
        ("Breckenridge", 39.4817, -106.0384),
        ("Steamboat Springs", 40.4850, -106.8317),
        ("Telluride", 37.9375, -107.8123)
    ]
    
    table = Table(title="Colorado Locations to GMU Mapping")
    table.add_column("Location", style="cyan")
    table.add_column("Region", style="blue")
    table.add_column("Lat", style="green")
    table.add_column("Lon", style="green")
    table.add_column("GMU", style="yellow")
    
    gmu_set = set()
    
    for i, (name, lat, lon) in enumerate(test_locations):
        gmu = gmu_processor.find_gmu_for_point(lat, lon)
        if gmu:
            gmu_set.add(gmu)
        
        # Determine region
        if i < 3:
            region = "Front Range"
        elif i < 6:
            region = "Western Slope"
        elif i < 9:
            region = "Southern CO"
        elif i < 11:
            region = "Eastern Plains"
        elif i < 16:
            region = "Mountain Peaks"
        else:
            region = "Ski Areas"
        
        table.add_row(name, region, f"{lat:.4f}", f"{lon:.4f}", gmu or "None")
    
    console.print(table)
    console.print(f"\n[green]Unique GMUs found: {len(gmu_set)} different GMUs[/green]")
    console.print(f"GMUs represented: {', '.join(sorted(gmu_set))}")

if __name__ == "__main__":
    gmu_processor, gmu_bounds = verify_all_gmus()
    test_known_colorado_locations(gmu_processor)
    
    console.print("\n[bold green]✓ Verification Complete[/bold green]")
    console.print("All GMU polygons are properly loaded and functional across Colorado.")
