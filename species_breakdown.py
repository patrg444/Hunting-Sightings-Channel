#!/usr/bin/env python3
import psycopg2
from datetime import datetime

# Database connection
SUPABASE_DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:***REMOVED***@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

print("=" * 60)
print("SPECIES BREAKDOWN OF ALL SIGHTINGS")
print("=" * 60)

# Total sightings
cur.execute("SELECT COUNT(*) FROM sightings")
total = cur.fetchone()[0]
print(f"\nTotal sightings in database: {total}")

# Species breakdown
print("\n--- Sightings by Species ---")
cur.execute("""
    SELECT species, COUNT(*) as count
    FROM sightings
    GROUP BY species
    ORDER BY count DESC
""")

species_data = cur.fetchall()
for species, count in species_data:
    percentage = (count / total) * 100
    print(f"{species:20s}: {count:4d} ({percentage:5.1f}%)")

# Species with coordinates (on map)
print("\n--- Species with Coordinates (visible on map) ---")
cur.execute("""
    SELECT species, 
           COUNT(*) as total_count,
           COUNT(CASE WHEN location IS NOT NULL THEN 1 END) as with_coords,
           ROUND(100.0 * COUNT(CASE WHEN location IS NOT NULL THEN 1 END) / COUNT(*), 1) as percent_mapped
    FROM sightings
    GROUP BY species
    ORDER BY total_count DESC
""")

mapped_data = cur.fetchall()
for species, total_count, with_coords, percent_mapped in mapped_data:
    print(f"{species:20s}: {with_coords:4d} of {total_count:4d} ({percent_mapped:5.1f}% mapped)")

# Recent sightings by species (last 30 days)
print("\n--- Recent Sightings by Species (last 30 days) ---")
cur.execute("""
    SELECT species, COUNT(*) as count
    FROM sightings
    WHERE sighting_date >= NOW() - INTERVAL '30 days'
    GROUP BY species
    ORDER BY count DESC
""")

recent_data = cur.fetchall()
if recent_data:
    for species, count in recent_data:
        print(f"{species:20s}: {count:4d}")
else:
    print("No sightings in the last 30 days")

# Source breakdown by species
print("\n--- Top Species by Source ---")
cur.execute("""
    SELECT source_type, species, COUNT(*) as count
    FROM sightings
    WHERE source_type IN (
        SELECT source_type 
        FROM sightings 
        GROUP BY source_type 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    )
    GROUP BY source_type, species
    ORDER BY source_type, count DESC
""")

current_source = None
source_data = cur.fetchall()
for source, species, count in source_data:
    if source != current_source:
        print(f"\n{source}:")
        current_source = source
    print(f"  {species:18s}: {count:4d}")

cur.close()
conn.close()