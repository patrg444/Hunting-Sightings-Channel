-- Wildlife Sightings Database Schema
-- PostgreSQL with PostGIS extension

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,  -- References Supabase auth.users
    email_notifications BOOLEAN DEFAULT true,
    notification_time TIME DEFAULT '06:00:00',
    gmu_filter INTEGER[] DEFAULT '{}',
    species_filter TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Wildlife sightings table
CREATE TABLE IF NOT EXISTS sightings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    species TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    keyword_matched TEXT,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    trail_name TEXT,
    sighting_date TIMESTAMP WITH TIME ZONE,
    gmu_unit INTEGER,
    location GEOGRAPHY(POINT, 4326),
    confidence_score FLOAT DEFAULT 1.0,
    reddit_post_title TEXT,
    subreddit TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- GMU polygons table
CREATE TABLE IF NOT EXISTS gmus (
    id INTEGER PRIMARY KEY,  -- GMU number
    name TEXT NOT NULL,
    geometry GEOGRAPHY(POLYGON, 4326) NOT NULL
);

-- Trail index table
CREATE TABLE IF NOT EXISTS trails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source TEXT,
    geometry GEOGRAPHY(LINESTRING, 4326),
    gmu_units INTEGER[],
    elevation_gain INTEGER,
    distance_miles FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sightings_date ON sightings(sighting_date DESC);
CREATE INDEX idx_sightings_gmu ON sightings(gmu_unit);
CREATE INDEX idx_sightings_species ON sightings(species);
CREATE INDEX idx_sightings_source ON sightings(source_type);
CREATE INDEX idx_sightings_location ON sightings USING GIST(location);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

CREATE INDEX idx_trails_name ON trails(name);
CREATE INDEX idx_trails_gmu_units ON trails USING GIN(gmu_units);

CREATE INDEX idx_gmus_geometry ON gmus USING GIST(geometry);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for user_preferences
CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data insertion for GMUs (simplified boundaries)
-- In production, import full GMU polygons from Colorado Parks & Wildlife
INSERT INTO gmus (id, name, geometry) VALUES
(12, 'GMU 12', ST_GeogFromText('POLYGON((-105.8 39.9, -105.5 39.9, -105.5 39.6, -105.8 39.6, -105.8 39.9))')),
(201, 'GMU 201', ST_GeogFromText('POLYGON((-106.3 39.7, -106.0 39.7, -106.0 39.4, -106.3 39.4, -106.3 39.7))'))
ON CONFLICT (id) DO NOTHING;
