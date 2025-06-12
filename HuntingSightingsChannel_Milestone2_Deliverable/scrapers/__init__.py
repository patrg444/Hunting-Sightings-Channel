"""
Web scrapers for extracting wildlife sightings from various outdoor recreation websites.
"""

from .base import BaseScraper
from .fourteeners_scraper import FourteenersScraper
from .summitpost_scraper import SummitPostScraper
from .reddit_scraper import RedditScraper

__all__ = [
    'BaseScraper',
    'FourteenersScraper', 
    'SummitPostScraper',
    'RedditScraper'
]
