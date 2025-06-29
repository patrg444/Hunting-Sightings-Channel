-- Query to check for duplicate sightings based on specific criteria
-- Looking for entries with:
-- 1. Same date (Jun 27, 2025)
-- 2. Same species (Elk)
-- 3. Same source (14ers)
-- 4. No GMU (NULL or empty)

-- First, let's see all sightings matching these criteria
SELECT 
    id,
    species,
    date,
    source,
    gmu,
    latitude,
    longitude,
    location_description,
    notes,
    created_at
FROM sightings
WHERE 
    date = '2025-06-27'
    AND species = 'Elk'
    AND source = '14ers'
    AND (gmu IS NULL OR gmu = '')
ORDER BY id;

-- Count how many entries match these criteria
SELECT 
    COUNT(*) as matching_entries
FROM sightings
WHERE 
    date = '2025-06-27'
    AND species = 'Elk'
    AND source = '14ers'
    AND (gmu IS NULL OR gmu = '');

-- Check for duplicates with same coordinates
SELECT 
    latitude,
    longitude,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(id) as duplicate_ids,
    GROUP_CONCAT(location_description, ' | ') as locations,
    GROUP_CONCAT(notes, ' | ') as all_notes
FROM sightings
WHERE 
    date = '2025-06-27'
    AND species = 'Elk'
    AND source = '14ers'
    AND (gmu IS NULL OR gmu = '')
GROUP BY latitude, longitude
HAVING COUNT(*) > 1;

-- Show all potential duplicates side by side for comparison
SELECT 
    s1.id as id1,
    s2.id as id2,
    s1.latitude as lat1,
    s2.latitude as lat2,
    s1.longitude as lon1,
    s2.longitude as lon2,
    s1.location_description as location1,
    s2.location_description as location2,
    s1.notes as notes1,
    s2.notes as notes2,
    s1.created_at as created1,
    s2.created_at as created2
FROM sightings s1
JOIN sightings s2 ON 
    s1.date = s2.date
    AND s1.species = s2.species
    AND s1.source = s2.source
    AND (s1.gmu IS NULL OR s1.gmu = '')
    AND (s2.gmu IS NULL OR s2.gmu = '')
    AND s1.id < s2.id  -- Avoid duplicate pairs
WHERE 
    s1.date = '2025-06-27'
    AND s1.species = 'Elk'
    AND s1.source = '14ers'
    AND (s1.gmu IS NULL OR s1.gmu = '');

-- Summary of all matching entries grouped by key fields
SELECT 
    date,
    species,
    source,
    COALESCE(gmu, 'NULL') as gmu_value,
    COUNT(*) as entry_count,
    COUNT(DISTINCT latitude || ',' || longitude) as unique_locations,
    GROUP_CONCAT(DISTINCT id ORDER BY id) as all_ids
FROM sightings
WHERE 
    date = '2025-06-27'
    AND species = 'Elk'
    AND source = '14ers'
    AND (gmu IS NULL OR gmu = '')
GROUP BY date, species, source, gmu;