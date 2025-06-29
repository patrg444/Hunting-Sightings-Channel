# Hunting Sightings Channel - Source Breakdown Report

## Executive Summary
The database contains **794 wildlife sightings** from 5 different sources, with Reddit being the dominant contributor (72.4%).

## 1. Source Distribution

| Source | Total Sightings | Percentage | Date Range |
|--------|----------------|------------|------------|
| **Reddit** | 575 | 72.4% | Apr 30 - Jun 28, 2025 |
| **14ers.com** | 89 | 11.2% | Jun 7 - Jun 27, 2025 |
| **SummitPost** | 86 | 10.8% | Jun 7 - Jun 27, 2025 |
| **iNaturalist** | 31 | 3.9% | May 26 - Jun 26, 2025 |
| **Google Places** | 13 | 1.6% | Jul 5, 2024 - Jun 23, 2025 |

## 2. Data Quality by Source

### Coordinate Coverage
- **iNaturalist**: 96.8% (best coverage - GPS-based observations)
- **Reddit**: 33.0% (many posts lack specific locations)
- **Google Places**: 7.7%
- **14ers.com**: 5.6%
- **SummitPost**: 1.2%

### Location Confidence Radius
- **Reddit**: 58.3% (only source with radius data)
- **Others**: 0% (need to process these sources)

### Average Confidence Scores
1. **iNaturalist**: 0.998 (highest - verified observations)
2. **SummitPost**: 0.842
3. **Google Places**: 0.819
4. **Reddit**: 0.804
5. **14ers.com**: 0.755

## 3. Species Distribution by Source

### Reddit (575 sightings)
- Bear: 247 (43.0%)
- Deer: 233 (40.5%)
- Elk: 70 (12.2%)
- Others: 25 (4.3%)

### 14ers.com (89 sightings)
- Bighorn Sheep: 30 (33.7%)
- Elk: 28 (31.5%)
- Deer: 15 (16.9%)
- Mountain Goat: 7 (7.9%)
- Bear: 6 (6.7%)

### SummitPost (86 sightings)
- Elk: 24 (27.9%)
- Deer: 13 (15.1%)
- Bighorn Sheep: 11 (12.8%)
- Black Bear: 11 (12.8%)
- Mountain Goat: 8 (9.3%)

### iNaturalist (31 sightings)
- Black Bear: 30 (96.8%)
- Other: 1 (3.2%)

### Google Places (13 sightings)
- Elk: 5 (38.5%)
- Bighorn Sheep: 3 (23.1%)
- Deer: 2 (15.4%)
- Bear: 2 (15.4%)

## 4. Geographic Coverage

### Unique Locations by Source
1. **Reddit**: 208 locations (broadest coverage)
2. **iNaturalist**: 28 locations
3. **SummitPost**: 17 locations
4. **14ers.com**: 12 locations
5. **Google Places**: 9 locations

### Top Locations
- **Reddit**: Unknown (111), Estes Park (18), RMNP (16)
- **14ers**: Humboldt Peak (26), Rio Grande Pyramid (26)
- **SummitPost**: Capitol Peak (17), Mount Evans (8)
- **iNaturalist**: Colorado, US (4)
- **Google Places**: Bighorn Trailhead (3)

## 5. Recent Activity (Last 30 Days)
- **Reddit**: 415 sightings (most active)
- **14ers.com**: 89 sightings
- **SummitPost**: 86 sightings
- **iNaturalist**: 30 sightings
- **Google Places**: 5 sightings

## Key Insights

1. **Reddit Dominance**: 72.4% of all sightings come from Reddit, making it the primary data source

2. **Species Patterns**:
   - Reddit focuses on common species (bear, deer, elk)
   - Mountain-focused sources (14ers, SummitPost) have more alpine species (bighorn sheep, mountain goats)
   - iNaturalist is almost exclusively black bear observations

3. **Data Quality Issues**:
   - Only 28.6% of all sightings have coordinates
   - Reddit has the best radius data (58.3%) but poor coordinate coverage (33%)
   - iNaturalist has excellent coordinates (96.8%) but no radius data

4. **Geographic Patterns**:
   - 111 Reddit sightings have "Unknown" location
   - Mountain sources concentrate on specific peaks
   - iNaturalist has precise GPS coordinates

## Recommendations

1. **Improve Geocoding**: Focus on the 111 "Unknown" Reddit locations
2. **Add Radius Data**: Process non-Reddit sources to add location confidence radius
3. **Enhance Coordinate Coverage**: Improve coordinate extraction for 14ers and SummitPost
4. **Source Diversification**: Consider adding more GPS-based sources like iNaturalist