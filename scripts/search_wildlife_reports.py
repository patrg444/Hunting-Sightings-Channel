#!/usr/bin/env python3
"""
Script to search through multiple 14ers.com trip reports for actual wildlife sightings.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.fourteeners_scraper_real import FourteenersRealScraper


def search_for_wildlife_reports(days_back: int = 30):
    """Search through recent trip reports to find ones with potential wildlife sightings."""
    logger.info(f"Searching for wildlife sightings in reports from the past {days_back} days...")
    
    # Create scraper instance
    scraper = FourteenersRealScraper()
    
    # Get recent trip reports
    reports = scraper._get_recent_trip_reports_real(lookback_days=days_back)
    logger.info(f"Found {len(reports)} trip reports to analyze")
    
    # Track reports with sightings
    reports_with_sightings = []
    all_sightings = []
    
    # Analyze each report
    for i, report in enumerate(reports):
        logger.info(f"\nAnalyzing report {i+1}/{len(reports)}: {report['title']}")
        
        # Extract sightings
        sightings = scraper._extract_sightings_from_report(report)
        
        if sightings:
            # Filter out obvious false positives
            real_sightings = []
            for sighting in sightings:
                context = sighting['raw_text'].lower()
                keyword = sighting['keyword_matched'].lower()
                
                # Known false positive patterns
                false_positives = [
                    'black bear pass',
                    'grizzly peak',
                    'deer creek',
                    'elk mountain',
                    'bear lake',
                    'goat rocks',
                    'sheep mountain',
                    'antelope',  # Often part of "Antelope Springs" or similar
                    'crampons',  # Contains "ram"
                    'drama',     # Contains "ram"
                    'program',   # Contains "ram"
                    'panorama',  # Contains "ram"
                ]
                
                # Check if this is a false positive
                is_false_positive = False
                for fp in false_positives:
                    if fp in context:
                        is_false_positive = True
                        break
                
                # Additional checks for real sightings
                positive_indicators = [
                    'saw', 'spotted', 'watched', 'encountered',
                    'ran into', 'came across', 'crossing',
                    'grazing', 'feeding', 'tracks', 'scat',
                    'herd', 'bull', 'cow', 'buck', 'doe'
                ]
                
                has_positive_indicator = any(indicator in context for indicator in positive_indicators)
                
                if not is_false_positive and (has_positive_indicator or len(context) > 40):
                    real_sightings.append(sighting)
                    logger.success(f"  REAL SIGHTING: {sighting['species']} - '{context}'")
                else:
                    logger.debug(f"  False positive: {sighting['species']} - '{context}'")
            
            if real_sightings:
                reports_with_sightings.append({
                    'report': report,
                    'sightings': real_sightings,
                    'count': len(real_sightings)
                })
                all_sightings.extend(real_sightings)
        
        # Rate limit
        time.sleep(0.5)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total reports analyzed: {len(reports)}")
    logger.info(f"Reports with real wildlife sightings: {len(reports_with_sightings)}")
    logger.info(f"Total real wildlife sightings found: {len(all_sightings)}")
    
    if reports_with_sightings:
        logger.info("\nReports with wildlife sightings:")
        for item in sorted(reports_with_sightings, key=lambda x: x['count'], reverse=True):
            report = item['report']
            logger.info(f"\n{report['title']} ({report['date'].strftime('%m/%d/%Y')})")
            logger.info(f"  URL: {report['url']}")
            logger.info(f"  Author: {report['author']}")
            logger.info(f"  Sightings: {item['count']}")
            
            for sighting in item['sightings']:
                logger.info(f"    - {sighting['species']}: {sighting['raw_text']}")
    
    # Save results
    if all_sightings:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'wildlife_sightings_{timestamp}.json'
        
        import json
        with open(filename, 'w') as f:
            json.dump({
                'search_date': datetime.now().isoformat(),
                'days_searched': days_back,
                'reports_analyzed': len(reports),
                'reports_with_sightings': len(reports_with_sightings),
                'total_sightings': len(all_sightings),
                'sightings': [
                    {
                        'species': sighting['species'],
                        'raw_text': sighting['raw_text'],
                        'keyword_matched': sighting['keyword_matched'],
                        'source_url': sighting['source_url'],
                        'trail_name': sighting.get('trail_name', ''),
                        'author': sighting.get('author', ''),
                        'report_title': sighting.get('report_title', ''),
                        'sighting_date': sighting['sighting_date'].isoformat() if isinstance(sighting['sighting_date'], datetime) else str(sighting['sighting_date'])
                    }
                    for sighting in all_sightings
                ]
            }, f, indent=2)
        
        logger.info(f"\nResults saved to {filename}")


def main():
    """Main function."""
    # Search the last 30 days by default
    days = 30
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    
    search_for_wildlife_reports(days)


if __name__ == "__main__":
    main()
