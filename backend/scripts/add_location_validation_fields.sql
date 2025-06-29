-- Add location validation fields to wildlife_sightings table
ALTER TABLE wildlife_sightings
ADD COLUMN IF NOT EXISTS location_validation_confidence FLOAT,
ADD COLUMN IF NOT EXISTS location_validation_issues JSONB;

-- Add index for finding problematic entries
CREATE INDEX IF NOT EXISTS idx_location_validation_confidence 
ON wildlife_sightings(location_validation_confidence) 
WHERE location_validation_confidence IS NOT NULL;

-- Comment on new columns
COMMENT ON COLUMN wildlife_sightings.location_validation_confidence IS 'Confidence score (0-1) that location assignment is correct';
COMMENT ON COLUMN wildlife_sightings.location_validation_issues IS 'JSON array of validation issues found';