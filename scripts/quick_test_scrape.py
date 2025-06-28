#!/usr/bin/env python3
"""
Quick test scrape with shorter lookback period to verify everything works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fresh_scrape_all import run_all_scrapers, print_summary
from loguru import logger

def main():
    """Run quick test scrape with 7-day lookback."""
    
    logger.info("=" * 60)
    logger.info("QUICK TEST SCRAPE (7 days)")
    logger.info("Verifying all scrapers work with new format")
    logger.info("=" * 60)
    
    # Run with just 7 days for quick test
    results = run_all_scrapers(lookback_days=7)
    
    # Print summary
    print_summary(results)
    
    # Check if all sources have location_confidence_radius
    logger.info("\nVerifying location_confidence_radius presence:")
    for source, stats in results['sources'].items():
        if 'error' not in stats:
            if stats['total_found'] > 0:
                radius_pct = stats['with_radius'] / stats['total_found'] * 100
                if radius_pct < 90:
                    logger.warning(f"  {source}: Only {radius_pct:.1f}% have radius!")
                else:
                    logger.success(f"  {source}: {radius_pct:.1f}% have radius ✓")

if __name__ == "__main__":
    main()