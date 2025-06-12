#!/usr/bin/env python3
"""
Debug script to test GMU mapping functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors import GMUProcessor, TrailProcessor
from rich.console import Console
from rich.table import Table
import json

console = Console()

def test_gmu_files():
    """Test different GMU files to see which has proper coverage"""
    
    gmu_files = [
        "data/gmu/colorado_gmu_sample.geojson",
        "data/gmu/colorado_gmu.geojson",
        "data/gmu/colorado_gmu_simplified.geojson"
    ]
    
    # Load trail data to get test coordinates
    trail_processor = TrailProcessor()
    trail_processor.load_trail_index()
    
    console.print("[bold]Testing GMU Files Coverage[/bold]\n")
    
    for gmu_file in gmu_files:
        if not os.path.exists(gmu_file):
            console.print(f"[red]File not found: {gmu_file}[/red]")
            continue
            
        console.print(f"\n[yellow]Testing: {gmu_file}[/yellow]")
        
        try:
            # Load GMU processor with this file
            gmu_processor = GMUProcessor(gmu_file)
            gmu_processor.load_gmu_data()
            
            # Check file contents
            with open(gmu_file, 'r') as f:
                data = json.load(f)
                feature_count = len(data.get('features', []))
                console.print(f"  GMU polygons in file: {feature_count}")
            
            # Test mapping with some trail locations
            mapped_count = 0
            test_trails = trail_processor.trails[:5] if trail_processor.trails else []
            
            table = Table(title=f"Trail to GMU Mapping Test")
            table.add_column("Trail", style="cyan")
            table.add_column("Lat", style="green")
            table.add_column("Lon", style="green")
            table.add_column("GMU", style="yellow")
            
            for trail in test_trails:
                if 'lat' in trail and 'lon' in trail:
                    gmu = gmu_processor.find_gmu_for_point(trail['lat'], trail['lon'])
                    if gmu:
                        mapped_count += 1
                    table.add_row(
                        trail['name'],
                        f"{trail['lat']:.4f}",
                        f"{trail['lon']:.4f}",
                        gmu or "Not Found"
                    )
            
            console.print(table)
            console.print(f"  Successfully mapped: {mapped_count}/{len(test_trails)} trails")
            
        except Exception as e:
            console.print(f"[red]Error loading {gmu_file}: {e}[/red]")

def test_specific_coordinates():
    """Test specific coordinates to verify GMU boundaries"""
    
    console.print("\n[bold]Testing Specific Coordinates[/bold]\n")
    
    # Test coordinates from known Colorado locations
    test_points = [
        ("Mount Elbert", 39.1178, -106.4453),
        ("Mount Evans", 39.5883, -105.6438),
        ("Pikes Peak", 38.8409, -105.0422),
        ("Denver", 39.7392, -104.9903),
        ("Aspen", 39.1911, -106.8175)
    ]
    
    # Test with full GMU file
    gmu_file = "data/gmu/colorado_gmu.geojson"
    if os.path.exists(gmu_file):
        gmu_processor = GMUProcessor(gmu_file)
        gmu_processor.load_gmu_data()
        
        table = Table(title="Coordinate to GMU Mapping")
        table.add_column("Location", style="cyan")
        table.add_column("Lat", style="green")
        table.add_column("Lon", style="green")
        table.add_column("GMU", style="yellow")
        
        for name, lat, lon in test_points:
            gmu = gmu_processor.find_gmu_for_point(lat, lon)
            table.add_row(name, f"{lat:.4f}", f"{lon:.4f}", gmu or "Not Found")
        
        console.print(table)
    else:
        console.print(f"[red]Full GMU file not found: {gmu_file}[/red]")

def check_gmu_bounds():
    """Check the bounds of GMUs in each file"""
    
    console.print("\n[bold]GMU Boundary Analysis[/bold]\n")
    
    gmu_files = [
        "data/gmu/colorado_gmu_sample.geojson",
        "data/gmu/colorado_gmu.geojson"
    ]
    
    for gmu_file in gmu_files:
        if not os.path.exists(gmu_file):
            continue
            
        console.print(f"\n[yellow]{gmu_file}:[/yellow]")
        
        with open(gmu_file, 'r') as f:
            data = json.load(f)
            
        for feature in data.get('features', [])[:5]:  # Show first 5 GMUs
            props = feature.get('properties', {})
            gmu_id = props.get('GMUID', props.get('DAU', 'Unknown'))
            gmu_name = props.get('NAME', 'Unknown')
            
            # Calculate bounds
            coords = feature['geometry']['coordinates'][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            
            console.print(f"  GMU {gmu_id} ({gmu_name}):")
            console.print(f"    Lat range: {min(lats):.4f} to {max(lats):.4f}")
            console.print(f"    Lon range: {min(lons):.4f} to {max(lons):.4f}")

if __name__ == "__main__":
    test_gmu_files()
    test_specific_coordinates()
    check_gmu_bounds()
