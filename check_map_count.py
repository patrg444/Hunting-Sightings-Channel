#!/usr/bin/env python3
import psycopg2

# Database connection
SUPABASE_DB_URL = "postgresql://postgres.rvrdbtrxwndeerqmziuo:***REMOVED***@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM sightings WHERE location IS NOT NULL")
with_coords = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM sightings")
total = cur.fetchone()[0]

print(f"Total sightings in database: {total}")
print(f"Sightings with coordinates (on map): {with_coords}")
print(f"Percentage on map: {with_coords/total*100:.1f}%")

cur.close()
conn.close()