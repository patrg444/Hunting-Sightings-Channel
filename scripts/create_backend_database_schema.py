#!/usr/bin/env python3
"""
Create or update the backend PostgreSQL database schema to match what the backend expects.
This script creates the proper tables for the FastAPI backend.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

def create_database_if_not_exists(connection_params):
    """Create the database if it doesn't exist."""
    # Connect to postgres database to check/create our database
    conn = psycopg2.connect(
        host=connection_params['host'],
        port=connection_params['port'],
        user=connection_params['user'],
        password=connection_params['password'],
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (connection_params['database'],)
    )
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(f"CREATE DATABASE {connection_params['database']}")
        logger.info(f"Created database: {connection_params['database']}")
    else:
        logger.info(f"Database already exists: {connection_params['database']}")
    
    cursor.close()
    conn.close()

def create_schema():
    """Create the backend database schema."""
    
    # Parse database URL from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hunting_sightings')
    
    # Parse connection parameters
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    
    connection_params = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username or 'postgres',
        'password': parsed.password or 'postgres',
        'database': parsed.path.lstrip('/') or 'hunting_sightings'
    }
    
    # Create database if needed
    create_database_if_not_exists(connection_params)
    
    # Connect to our database
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor()
    
    try:
        # Enable PostGIS extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        logger.info("Enabled required extensions")
        
        # Create sightings table with all required fields
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sightings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            species VARCHAR(50) NOT NULL,
            raw_text TEXT NOT NULL,
            keyword_matched VARCHAR(50),
            source_url TEXT NOT NULL,
            source_type VARCHAR(50) NOT NULL,
            extracted_at TIMESTAMP WITH TIME ZONE NOT NULL,
            trail_name VARCHAR(255),
            sighting_date TIMESTAMP WITH TIME ZONE,
            gmu_unit INTEGER,
            location GEOGRAPHY(POINT, 4326),
            confidence_score FLOAT DEFAULT 1.0,
            reddit_post_title TEXT,
            subreddit VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- Additional fields for compatibility
            location_confidence_radius FLOAT,
            content_hash TEXT UNIQUE
        );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sightings_species ON sightings(species);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sightings_source_type ON sightings(source_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sightings_gmu_unit ON sightings(gmu_unit);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sightings_sighting_date ON sightings(sighting_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sightings_location ON sightings USING GIST(location);")
        
        # Create user_preferences table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL UNIQUE,
            email_notifications BOOLEAN DEFAULT false,
            notification_time TIME DEFAULT '08:00:00',
            gmu_filter INTEGER[] DEFAULT '{}',
            species_filter VARCHAR(50)[] DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Create GMU table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gmus (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            geometry GEOGRAPHY(POLYGON, 4326)
        );
        """)
        
        # Create trails table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trails (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            source VARCHAR(50),
            geometry GEOGRAPHY(LINESTRING, 4326),
            gmu_units INTEGER[],
            elevation_gain INTEGER,
            distance_miles FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        logger.success("Database schema created successfully!")
        
        # Show table info
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_schema()