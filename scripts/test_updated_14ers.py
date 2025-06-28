#!/usr/bin/env python3
"""
Test script to verify the updated 14ers.com scrapers work with the current HTML structure.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.fourteeners_scraper_real import FourteenersRealScraper
# from scrapers.fourteeners_auth_scraper import FourteenersAuthScraper  # Deleted - use FourteenersRealScraper
from loguru import logger


def test_real_scraper():
    """Test the real scraper without authentication."""
    logger.info("Testing FourteenersRealScraper...")
    
    scraper = FourteenersRealScraper()
    
    # Test getting recent trip reports
    logger.info("Testing _get_recent_trip_reports_real method...")
    reports = scraper._get_recent_trip_reports_real(lookback_days=7)
    
    if reports:
        logger.success(f"Found {len(reports)} trip reports!")
        for i, report in enumerate(reports[:3]):  # Show first 3
            logger.info(f"Report {i+1}:")
            logger.info(f"  Title: {report['title']}")
            logger.info(f"  URL: {report['url']}")
            logger.info(f"  Date: {report['date']}")
            logger.info(f"  Peaks: {report['peaks']}")
            logger.info(f"  Author: {report.get('author', 'Unknown')}")
        
        # Test extracting sightings from first report
        if reports:
            logger.info("\nTesting sighting extraction from first report...")
            sightings = scraper._extract_sightings_from_report(reports[0])
            
            if sightings:
                logger.success(f"Found {len(sightings)} wildlife sightings!")
                for sighting in sightings:
                    logger.info(f"Wildlife: {sighting['species']} - {sighting['raw_text']}")
                    logger.info(f"  Keyword matched: {sighting['keyword_matched']}")
            else:
                logger.info("No wildlife sightings found in the first report")
    else:
        logger.warning("No trip reports found - the HTML structure might have changed")
    
    # Test full scrape
    logger.info("\nTesting full scrape method...")
    all_sightings = scraper.scrape(lookback_days=7)
    logger.info(f"Total sightings found: {len(all_sightings)}")


def test_auth_scraper():
    """Test the authenticated scraper."""
    logger.info("\n" + "="*50)
    logger.info("Testing FourteenersAuthScraper...")
    
    scraper = FourteenersAuthScraper()
    
    # Test login
    logger.info("Testing login...")
    login_success = scraper._login()
    
    if login_success:
        logger.success("Login successful!")
        
        # Test getting reports with authentication
        logger.info("\nTesting authenticated report fetching...")
        reports = scraper._get_recent_trip_reports(lookback_days=7)
        
        if reports:
            logger.success(f"Found {len(reports)} trip reports with authentication!")
            logger.info(f"First report: {reports[0]['title']}")
        else:
            logger.warning("No reports found with authentication")
    else:
        logger.error("Login failed - check credentials or login form structure")


def main():
    """Run all tests."""
    logger.info("Testing updated 14ers.com scrapers...")
    logger.info("="*50)
    
    # Test real scraper first
    test_real_scraper()
    
    # Then test authenticated scraper
    test_auth_scraper()
    
    logger.info("\n" + "="*50)
    logger.info("Testing complete!")


if __name__ == "__main__":
    main()
