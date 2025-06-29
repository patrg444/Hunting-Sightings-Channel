# Location Validation Implementation

## Problem Addressed

A critical data accuracy issue was discovered where wildlife sightings from other states were being incorrectly assigned Colorado GMUs and coordinates. For example, a sighting explicitly stating "I live in Mass. and the camera is in Virginia" was assigned to Colorado GMU 46.

## Solution Implemented

### 1. LocationValidator Class (`backend/validators/location_validator.py`)

A comprehensive validation system that:
- Extracts state mentions from text (full names, abbreviations like "VA", "Mass.")
- Validates coordinates are within Colorado bounds (36-42°N, -109.5 to -102°W)
- Assigns confidence scores to location assignments
- Flags cross-state assignment errors

Key features:
- Handles all US state names and common abbreviations
- Special handling for punctuated abbreviations (e.g., "N.H.", "Mass.")
- Returns validation results with confidence scores and specific issues

### 2. LLM Validator Updates (`scrapers/llm_validator.py`)

Enhanced the LLM prompts to:
- Only assign coordinates for explicitly Colorado locations
- Return None for out-of-state or ambiguous locations
- Look for state indicators in text
- Validate assignments post-extraction

### 3. Validation Script (`backend/scripts/validate_sighting_locations.py`)

A utility script to:
- Scan existing database entries for location issues
- Generate detailed validation reports
- Optionally fix severe misassignments (confidence < 0.2)
- Find specific problematic entries

Usage:
```bash
# Generate validation report
python backend/scripts/validate_sighting_locations.py

# Fix severe issues
python backend/scripts/validate_sighting_locations.py --fix

# Find Virginia/Massachusetts entries
python backend/scripts/validate_sighting_locations.py --find-specific
```

### 4. Database Schema Updates

Added validation tracking fields:
- `location_validation_confidence` - Float (0-1) confidence score
- `location_validation_issues` - JSONB array of validation issues

## Testing

Comprehensive test suite (`backend/tests/test_location_validator.py`) validates:
- State extraction from various text formats
- Colorado boundary checking
- Complete location assignment validation
- Edge cases and special formats

All tests passing ✓

## Impact

This implementation:
1. Prevents future cross-state assignment errors
2. Provides tools to identify and fix existing bad data
3. Adds transparency with confidence scores and issue tracking
4. Maintains data quality standards

## Next Steps

1. Run validation script on production database
2. Review and fix flagged entries
3. Monitor new entries for validation issues
4. Consider adding UI indicators for low-confidence locations