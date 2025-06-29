"""
AWS Lambda handler for daily wildlife scraping.
"""

import json
from loguru import logger
from .reddit_scraper import RedditScraper
from .inaturalist_scraper import INaturalistScraper
from .database_saver import save_sightings_to_db

def lambda_handler(event, context):
    """Lambda handler function for daily scraping."""
    logger.info("Starting daily wildlife scraping...")
    
    results = {
        'reddit': {'found': 0, 'saved': 0},
        'inaturalist': {'found': 0, 'saved': 0},
        'total_found': 0,
        'total_saved': 0
    }
    
    try:
        # Run Reddit scraper
        logger.info("Running Reddit scraper...")
        reddit = RedditScraper()
        reddit_sightings = reddit.scrape(lookback_days=1)
        results['reddit']['found'] = len(reddit_sightings)
        logger.info(f"Found {len(reddit_sightings)} Reddit sightings")
        
        # Run iNaturalist scraper
        logger.info("Running iNaturalist scraper...")
        inat = INaturalistScraper()
        inat_sightings = inat.scrape(lookback_days=1)
        results['inaturalist']['found'] = len(inat_sightings)
        logger.info(f"Found {len(inat_sightings)} iNaturalist sightings")
        
        # Calculate totals
        results['total_found'] = results['reddit']['found'] + results['inaturalist']['found']
        
        # Count saved (already handled by scrapers)
        results['total_saved'] = results['total_found']  # Approximate
        
        logger.info(f"Daily scraping complete: {results['total_found']} total sightings")
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'results': results
            })
        }

# For local testing
if __name__ == "__main__":
    result = lambda_handler({}, {})
    print(json.dumps(result, indent=2))