#!/usr/bin/env python3
"""
Update Supabase PostgreSQL database schema to include new fields.
This script adds location_confidence_radius and content_hash fields.
"""

import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def update_schema():
    """Update the Supabase database schema with new fields."""
    
    # Parse Supabase database URL
    database_url = "postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
    
    logger.info("Connecting to Supabase database...")
    
    # Connect to database
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    try:
        # Check if sightings table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'sightings'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.error("Sightings table does not exist! Please create the base schema first.")
            return
        
        # Check current columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'sightings' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        existing_columns = {row[0]: row[1] for row in cursor.fetchall()}
        logger.info(f"Existing columns: {list(existing_columns.keys())}")
        
        # Add location_confidence_radius if it doesn't exist
        if 'location_confidence_radius' not in existing_columns:
            logger.info("Adding location_confidence_radius column...")
            cursor.execute("""
                ALTER TABLE sightings 
                ADD COLUMN location_confidence_radius FLOAT;
            """)
            logger.success("Added location_confidence_radius column")
        else:
            logger.info("location_confidence_radius column already exists")
        
        # Add content_hash if it doesn't exist
        if 'content_hash' not in existing_columns:
            logger.info("Adding content_hash column...")
            cursor.execute("""
                ALTER TABLE sightings 
                ADD COLUMN content_hash VARCHAR(32) UNIQUE;
            """)
            cursor.execute("CREATE INDEX idx_sightings_content_hash ON sightings(content_hash);")
            logger.success("Added content_hash column with unique constraint")
        else:
            logger.info("content_hash column already exists")
        
        # Commit changes
        conn.commit()
        logger.success("Schema updates completed successfully!")
        
        # Show updated schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'sightings' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        logger.info("\nUpdated sightings table schema:")
        for col_name, data_type, nullable in cursor.fetchall():
            logger.info(f"  {col_name}: {data_type} {'(nullable)' if nullable == 'YES' else '(required)'}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_schema()