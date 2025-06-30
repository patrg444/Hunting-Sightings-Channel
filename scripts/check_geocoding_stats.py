#!/usr/bin/env python3
import psycopg2

# Database connection
SUPABASE_DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:***REMOVED***@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

# Get all sightings with location names but no coordinates
cur.execute("""
    SELECT location_name, COUNT(*) as count
    FROM sightings 
    WHERE location IS NULL 
    AND location_name IS NOT NULL 
    AND length(location_name) > 0
    AND location_name != 'Unknown'
    GROUP BY location_name
    ORDER BY count DESC
""")

results = cur.fetchall()
total_needing_geocoding = sum(r[1] for r in results)

print(f"Total sightings with location names but no coordinates: {total_needing_geocoding}")
print(f"\nTop 20 location names needing geocoding:")
for i, (loc, count) in enumerate(results[:20]):
    print(f"{i+1:2d}. {loc[:50]:50s} - {count} sightings")

# Check how many were updated recently
cur.execute("""
    SELECT COUNT(*) 
    FROM sightings 
    WHERE location IS NOT NULL 
    AND updated_at > NOW() - INTERVAL '2 hours'
""")
recent = cur.fetchone()[0]
print(f"\nRecently geocoded (last 2 hours): {recent}")

cur.close()
conn.close()