# Hunting Sightings Channel - Corrected Source Breakdown

## Executive Summary
After removing unreliable SummitPost data, the database contains **708 wildlife sightings** from 4 legitimate sources.

## Source Distribution (Corrected)

| Source | Total Sightings | Percentage | Type |
|--------|----------------|------------|------|
| **Reddit** | 575 | 81.2% | User-submitted posts |
| **14ers.com** | 89 | 12.6% | Trip reports |
| **iNaturalist** | 31 | 4.4% | GPS-verified observations |
| **Google Places** | 13 | 1.8% | Reviews mentioning wildlife |
| ~~SummitPost~~ | ~~86~~ | ~~removed~~ | Test/invalid data |

## Key Statistics After Cleanup

### Overall Database
- **Total Sightings**: 708 (down from 794)
- **With Coordinates**: 227 of 708 (32.1%)
- **With Radius**: 335 of 708 (47.3%)
- **Unique Species**: 18

### Data Quality by Source
1. **iNaturalist**: 96.8% have coordinates (GPS-based)
2. **Reddit**: 33.0% have coordinates
3. **14ers.com**: 5.6% have coordinates
4. **Google Places**: 7.7% have coordinates

### Species Distribution (Top 5)
1. **Bear**: 285 sightings (40.3%)
2. **Deer**: 260 sightings (36.7%)
3. **Elk**: 127 sightings (17.9%)
4. **Bighorn Sheep**: 53 sightings (7.5%)
5. **Mountain Goat**: 20 sightings (2.8%)

## Data Quality Assessment

### Reliable Sources ✓
- **Reddit**: Large volume, community-verified
- **iNaturalist**: GPS coordinates, scientific observations
- **14ers.com**: Trip reports from hikers
- **Google Places**: Reviews with location context

### Removed Data ✗
- **SummitPost**: 86 records removed
  - All extracted on same day (June 27, 2025)
  - Generic, repetitive text snippets
  - Likely test data or scraping error

## Current Issues to Address

1. **Low Coordinate Coverage**: Only 32.1% of sightings have coordinates
2. **Unknown Locations**: 111 Reddit posts have "Unknown" location
3. **Missing Radius Data**: Only Reddit has location confidence radius
4. **Date Clustering**: Some sources have suspicious date patterns

## Next Steps

1. Process existing sightings to extract more coordinates
2. Add radius estimates for non-Reddit sources
3. Improve location extraction for "Unknown" Reddit posts
4. Implement better data validation for future scraping