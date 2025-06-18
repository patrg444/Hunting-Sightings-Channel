-- Additional tables for Google Places review processing
-- To be added to the existing database schema

-- Raw Google reviews table (30-day retention)
CREATE TABLE IF NOT EXISTS google_reviews_raw (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    review_data JSONB NOT NULL,  -- Full review JSON from Google
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT false,
    UNIQUE(place_id, review_id)  -- Prevent duplicate reviews
);

-- Wildlife events table for extracted sighting data
CREATE TABLE IF NOT EXISTS wildlife_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id TEXT NOT NULL,
    species TEXT NOT NULL,
    event_date DATE,  -- Date of the sighting (extracted from review)
    review_date DATE NOT NULL,  -- Date the review was posted
    source TEXT DEFAULT 'google_review',
    confidence_score FLOAT DEFAULT 1.0,
    gmu_unit INTEGER,
    location_details JSONB,  -- Additional location info extracted by NLP
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Google review ID cache for deduplication (permanent storage)
CREATE TABLE IF NOT EXISTS google_review_cache (
    review_id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (review_id, place_id)
);

-- Indexes for performance
CREATE INDEX idx_google_reviews_raw_fetched ON google_reviews_raw(fetched_at);
CREATE INDEX idx_google_reviews_raw_processed ON google_reviews_raw(processed);
CREATE INDEX idx_google_reviews_raw_place ON google_reviews_raw(place_id);

CREATE INDEX idx_wildlife_events_date ON wildlife_events(event_date DESC);
CREATE INDEX idx_wildlife_events_species ON wildlife_events(species);
CREATE INDEX idx_wildlife_events_place ON wildlife_events(place_id);
CREATE INDEX idx_wildlife_events_gmu ON wildlife_events(gmu_unit);

-- Function to clean up old raw reviews (to be called by scheduled job)
CREATE OR REPLACE FUNCTION cleanup_old_google_reviews() 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Move review IDs to cache before deletion
    INSERT INTO google_review_cache (review_id, place_id)
    SELECT review_id, place_id 
    FROM google_reviews_raw 
    WHERE fetched_at < NOW() - INTERVAL '30 days'
    ON CONFLICT (review_id, place_id) DO NOTHING;
    
    -- Delete old raw reviews
    DELETE FROM google_reviews_raw 
    WHERE fetched_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
