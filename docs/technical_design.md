# Hunting Sightings Channel - Technical Design Document

## System Architecture

### Overview
The Hunting Sightings Channel is an automated system that extracts wildlife sighting mentions from hiking trail reviews and maps them to Colorado Game Management Units (GMUs).

### Core Components

1. **Web Scrapers**
   - Base scraper class with rate limiting and error handling
   - Source-specific scrapers for 14ers.com, SummitPost, Reddit
   - Keyword-based sighting extraction (50-character window)

2. **Geospatial Processing**
   - GMU polygon management using GeoPandas
   - Point-in-polygon queries for trail/sighting location
   - Trail index with GMU mapping

3. **Data Storage**
   - PostgreSQL with PostGIS for spatial queries
   - Sighting records with 12-month retention
   - Trail index for location inference

4. **Email Digest System**
   - Daily HTML email generation
   - Sightings grouped by GMU and species
   - Scheduled via cron at 6 AM MT

### Data Flow

1. Scrapers run daily at 2 AM MT
2. Extract text containing game species keywords
3. Map sightings to GMUs using trail locations
4. Store validated sightings in database
5. Generate and send daily digest at 6 AM MT

## API Rate Limits and Compliance

### 14ers.com
- Rate limit: 1 request/second
- Robots.txt: Respected
- User-agent: Identifies bot and contact

### SummitPost.org
- Rate limit: 0.5 requests/second (conservative)
- No explicit API, parsing HTML
- Robots.txt: Respected

### Reddit API
- Official API with OAuth2
- Rate limit: 60 requests/minute (well under free tier)
- Compliance: Full API terms compliance

### Hiking Project
- Legacy JSON endpoints (post-OnX acquisition)
- API key required
- Rate limit: 1 request/second

## Terms of Service Notes

- All sources allow automated access with proper attribution
- No personal data collection
- Public content only (trail reviews, trip reports)
- Bot identification in User-Agent headers
- Contact information provided

## Infrastructure

### Development/MVP
- Single EC2 t3.small instance
- PostgreSQL on same instance
- Cron-based scheduling

### Production Scaling
- Lambda functions for scrapers
- RDS PostgreSQL instance
- S3 for HTML backup
- SES for email delivery

## Security Considerations

- API keys in environment variables
- Database credentials encrypted
- No storage of user personal data
- Read-only web scraping

## Monitoring

- Loguru for structured logging
- Email alerts for scraper failures
- Daily stats in digest footer
- S3 backup of raw HTML (30 days)

## Future Enhancements

1. **Phase 2: Expanded Species**
   - All wildlife mentions
   - Confidence scoring with NLP

2. **Phase 3: User Preferences**
   - Per-user GMU filtering
   - Species preferences
   - Custom delivery times

3. **Phase 4: Additional Sources**
   - AllTrails (with permission)
   - iNaturalist observations
   - Social media integration
