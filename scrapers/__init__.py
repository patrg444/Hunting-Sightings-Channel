"""
Web scrapers for extracting wildlife sightings from various outdoor recreation websites.
"""

from .base import BaseScraper
from .fourteeners_scraper_real import FourteenersRealScraper
from .reddit_scraper import RedditScraper
from .google_places_scraper import GooglePlacesScraper
from .inaturalist_scraper import INaturalistScraper

__all__ = [
    'BaseScraper',
    'FourteenersRealScraper', 
    'RedditScraper',
    'GooglePlacesScraper',
    'INaturalistScraper'
]
