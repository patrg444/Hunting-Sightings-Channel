#!/usr/bin/env python3
import psycopg2

# Database connection
SUPABASE_DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:***REMOVED***@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

print("MOOSE SIGHTINGS DETAILS")
print("="*60)

# Get all moose sightings
cur.execute("""
    SELECT 
        species,
        sighting_date,
        location_name,
        CASE WHEN location IS NOT NULL THEN 'Yes' ELSE 'No' END as has_coordinates,
        source_type,
        description,
        raw_text
    FROM sightings
    WHERE species = 'moose'
    ORDER BY sighting_date DESC
""")

moose_sightings = cur.fetchall()
print(f"\nTotal moose sightings: {len(moose_sightings)}\n")

for i, (species, date, location, has_coords, source, description, text) in enumerate(moose_sightings, 1):
    print(f"Sighting #{i}:")
    print(f"  Date: {date}")
    print(f"  Source: {source}")
    print(f"  Location: {location}")
    print(f"  Has coordinates: {has_coords}")
    print(f"  Description: {description}")
    if text:
        print(f"  Text preview: {text[:200]}...")
    print("-"*60)

# Check if there might be moose mentioned in other species fields
print("\nChecking for potential moose in other species or misclassified...")
cur.execute("""
    SELECT species, COUNT(*) as count
    FROM sightings
    WHERE raw_text ILIKE '%moose%' OR description ILIKE '%moose%'
    GROUP BY species
    ORDER BY count DESC
""")

potential_moose = cur.fetchall()
print(f"\nPosts mentioning 'moose' by species classification:")
for species, count in potential_moose:
    print(f"  {species}: {count}")

cur.close()
conn.close()