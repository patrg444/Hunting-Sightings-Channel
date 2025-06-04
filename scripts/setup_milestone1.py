#!/usr/bin/env python3
"""
Setup script for Milestone 1: GMU data and trail index.
Creates sample GMU polygons and aggregates trail data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from processors.gmu_processor import GMUProcessor
from processors.trail_processor import TrailProcessor
from loguru import logger


def setup_gmu_data():
    """Download/create GMU polygon data."""
    logger.info("Setting up GMU data...")
    
    gmu_processor = GMUProcessor("data/gmu/colorado_gmu_sample.geojson")
    
    # Create sample GMU data (in practice, this would download from CPW)
    gmu_processor.download_colorado_gmu_data()
    
    # Load and verify
    gmu_processor.load_gmu_data(target_gmus=["12", "201"])
    
    # Export simplified version for web use
    gmu_processor.export_simplified_geojson("data/gmu/colorado_gmu_simplified.geojson")
    
    return gmu_processor


def setup_trail_index(gmu_processor):
    """Aggregate trail data from various sources."""
    logger.info("Setting up trail index...")
    
    trail_processor = TrailProcessor()
    
    # Aggregate from different sources
    trail_processor.aggregate_14ers_trails()
    trail_processor.aggregate_summitpost_trails()
    
    # Map trails to GMUs
    trail_processor.map_trails_to_gmus(gmu_processor)
    
    # Save the index
    trail_processor.save_trail_index()
    
    # Export CSV version
    trail_processor.export_to_csv("data/trails/colorado_trails.csv")
    
    # Print statistics
    stats = trail_processor.get_trail_stats()
    logger.info(f"Trail statistics: {stats}")
    
    return trail_processor


def create_technical_design_doc():
    """Create the technical design document for Milestone 1."""
    logger.info("Creating technical design document...")
    
    design_doc = """# Hunting Sightings Channel - Technical Design Document

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
"""
    
    # Save the design document
    docs_path = Path("docs")
    docs_path.mkdir(exist_ok=True)
    
    with open(docs_path / "technical_design.md", "w") as f:
        f.write(design_doc)
    
    logger.info("Technical design document created at docs/technical_design.md")


def main():
    """Run the complete Milestone 1 setup."""
    logger.info("Starting Milestone 1 setup...")
    
    try:
        # Create necessary directories
        for dir_path in ["data/gmu", "data/trails", "data/raw", "logs", "docs"]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Setup GMU data
        gmu_processor = setup_gmu_data()
        
        # Setup trail index
        trail_processor = setup_trail_index(gmu_processor)
        
        # Create technical design document
        create_technical_design_doc()
        
        logger.success("Milestone 1 setup complete!")
        logger.info("Deliverables:")
        logger.info("- GMU polygons: data/gmu/colorado_gmu_sample.geojson")
        logger.info("- Trail index: data/trails/colorado_trails.json")
        logger.info("- Technical design: docs/technical_design.md")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
