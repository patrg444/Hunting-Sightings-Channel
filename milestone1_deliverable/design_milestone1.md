# Hunting Sightings Channel - Milestone 1 Design Document

## Tech Stack & Versions

- **Python**: 3.11
- **GeoPandas**: 0.14.0 (spatial operations)
- **Shapely**: 2.0.1 (point-in-polygon queries)
- **Pandas**: 2.1.0 (data processing)
- **Requests**: 2.31.0 (HTTP with proper User-Agent)
- **Loguru**: 0.7.2 (structured logging)

## Data Source Etiquette

### OpenStreetMap (Overpass API)
- **User-Agent**: "Hunting-Sightings-Channel/1.0 (contact@hunting-sightings.com)"
- **Rate limit**: 1 request/second (enforced with sleep)
- **Caching**: Raw JSON cached to `data/raw/` to minimize API hits
- **Timeout**: 20 minutes for large queries
- **Alternative**: overpass.kumi.systems if main throttles

### Colorado Parks & Wildlife
- **GMU data**: Public shapefile converted to GeoJSON
- **License**: Public domain
- **Attribution**: CPW Game Management Units

## Trail Index Rationale

We maintain a pre-computed trail/peak index (17,512 features) because:

1. **Text-only sources**: Trip reports mention "saw elk near Lost Creek Trail" without coordinates
2. **Performance**: Instant name→GMU lookups vs. repeated geocoding
3. **Coverage**: Complete Colorado trail/peak dataset with GMU mappings
4. **Efficiency**: One-time OSM pull cached for future use

## Roadmap: Milestones 2-4

### Milestone 2 (14ers + SummitPost + Reddit)
- Implement authenticated scrapers for trip reports
- Extract wildlife mentions using regex + LLM validation
- Map trail names to GMUs using our index
- Output: `wildlife_sightings.json` with structured data

### Milestone 3 (Email Digest System)
- PostgreSQL with PostGIS for spatial queries
- Daily/weekly digest generation
- User preferences (filter by GMU, species)
- SendGrid integration for delivery

### Milestone 4 (Advanced Features)
- Web dashboard with interactive GMU map
- Historical trend analysis
- Migration pattern detection
- API for mobile app integration

## Performance Metrics

- GMU lookup: ~50ms per point
- Trail index build: 25 seconds for 17,512 features
- OSM data pull: 18 seconds (60,909 elements)
- Total index generation: <1 minute

## Compliance Notes

All data sources accessed comply with their Terms of Service. We identify as a bot, respect rate limits, and only access public data. No personal information is collected or stored.
