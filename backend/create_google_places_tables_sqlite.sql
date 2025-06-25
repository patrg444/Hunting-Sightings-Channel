-- SQLite-compatible schema for Google Places wildlife extraction
-- Adapted from PostgreSQL schema for SQLite

-- Table for caching processed review IDs to avoid reprocessing
CREATE TABLE IF NOT EXISTS google_review_cache (
    review_id TEXT PRIMARY KEY,
    place_id TEXT NOT NULL,
    processed_at TEXT DEFAULT (datetime('now')),
    has_wildlife_mention INTEGER DEFAULT 0  -- SQLite uses INTEGER for boolean
);

-- Table for temporarily storing raw Google reviews (30-day retention)
CREATE TABLE IF NOT EXISTS google_reviews_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT UNIQUE NOT NULL,
    place_id TEXT NOT NULL,
    place_name TEXT NOT NULL,
    author_name TEXT,
    rating INTEGER,
    review_text TEXT NOT NULL,
    review_time TEXT,  -- Unix timestamp as text
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT DEFAULT (datetime('now', '+30 days'))
);

-- Table for permanent storage of extracted wildlife events
CREATE TABLE IF NOT EXISTS wildlife_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_review_id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    place_name TEXT NOT NULL,
    species TEXT NOT NULL,
    event_date TEXT,  -- Date when wildlife was observed
    review_date TEXT, -- Date when review was posted
    confidence_score REAL DEFAULT 0.0,
    gmu_unit TEXT,
    latitude REAL,
    longitude REAL,
    elevation_ft INTEGER,
    location_details TEXT,  -- JSON string for SQLite
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (source_review_id) REFERENCES google_review_cache(review_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_review_cache_place_id ON google_review_cache(place_id);
CREATE INDEX IF NOT EXISTS idx_reviews_raw_expires ON google_reviews_raw(expires_at);
CREATE INDEX IF NOT EXISTS idx_wildlife_events_species ON wildlife_events(species);
CREATE INDEX IF NOT EXISTS idx_wildlife_events_gmu ON wildlife_events(gmu_unit);
CREATE INDEX IF NOT EXISTS idx_wildlife_events_date ON wildlife_events(event_date);

-- Note: SQLite doesn't support stored procedures/functions like PostgreSQL
-- The cleanup of expired reviews needs to be done via Python script