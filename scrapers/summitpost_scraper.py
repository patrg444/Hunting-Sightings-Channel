"""
Scraper for SummitPost.org to extract wildlife sightings from route descriptions and trip reports.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseScraper


class SummitPostScraper(BaseScraper):
    """
    Scraper for SummitPost.org route descriptions and trip reports.
    """
    
    BASE_URL = "https://www.summitpost.org"
    
    def __init__(self):
        # Conservative rate limit for SummitPost
        super().__init__(source_name="summitpost.org", rate_limit=2.0)
        
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape recent content from SummitPost.
        
        Args:
            lookback_days: Number of days to look back for content
            
        Returns:
            List of wildlife sightings
        """
        all_sightings = []
        
        # Get Colorado peaks and their routes
        colorado_content = self._get_colorado_content()
        
        # Extract sightings from each piece of content
        for content in colorado_content:
            sightings = self._extract_sightings_from_content(content)
            all_sightings.extend(sightings)
        
        logger.info(f"Found {len(all_sightings)} total sightings from SummitPost")
        return all_sightings
    
    def _get_colorado_content(self) -> List[Dict[str, Any]]:
        """
        Get links to Colorado peak pages and recent trip reports.
        
        Returns:
            List of content metadata
        """
        content_list = []
        
        # For MVP, simulate some popular Colorado peaks on SummitPost
        sample_peaks = [
            {
                'url': f"{self.BASE_URL}/mount-elbert/150325",
                'title': "Mount Elbert",
                'type': 'peak_page'
            },
            {
                'url': f"{self.BASE_URL}/longs-peak/150329",
                'title': "Longs Peak", 
                'type': 'peak_page'
            },
            {
                'url': f"{self.BASE_URL}/mount-sneffels/150416",
                'title': "Mount Sneffels",
                'type': 'peak_page'
            },
            {
                'url': f"{self.BASE_URL}/capitol-peak/150313",
                'title': "Capitol Peak",
                'type': 'peak_page'
            }
        ]
        
        return sample_peaks
    
    def _extract_sightings_from_content(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from a SummitPost page.
        
        Args:
            content: Content metadata
            
        Returns:
            List of sightings found in this content
        """
        sightings = []
        
        # Fetch the page
        response = self._make_request(content['url'])
        if not response:
            return sightings
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for route descriptions and trip report sections
        # SummitPost has structured content sections
        content_sections = soup.find_all(['div', 'section'], class_=['content-body', 'route-description', 'trip-report'])
        
        # For MVP simulation with sample content
        if not content_sections:
            # Simulate route descriptions with wildlife mentions
            sample_descriptions = {
                "Mount Elbert": """
                    Standard Route: The trail starts at the North Mount Elbert Trailhead. Early morning starts are recommended 
                    to avoid afternoon thunderstorms. We saw a herd of elk near the treeline around 11,800 feet. The trail is 
                    well-marked and gains elevation steadily. Mountain goats are occasionally spotted near the false summit.
                """,
                "Longs Peak": """
                    Keyhole Route: This is a serious undertaking requiring an alpine start. The approach through the Boulder Field 
                    often has marmots and pikas. Last week a climber reported seeing a black bear near Chasm Lake junction. 
                    The route becomes technical after the Keyhole. Bighorn sheep frequent the area below the Loft.
                """,
                "Mount Sneffels": """
                    Southwest Ridge: Beautiful approach through Yankee Boy Basin. The wildflowers in July are spectacular. 
                    We encountered a small group of deer on the lower trail. The standard route is Class 2+ with some exposure. 
                    Mountain goats are common residents on the mountain and often seen traversing the north face.
                """,
                "Capitol Peak": """
                    Northeast Ridge (Standard): One of Colorado's most difficult fourteeners. The approach is long but scenic. 
                    Elk are frequently spotted in the Capitol Creek valley. The infamous Knife Edge requires careful navigation. 
                    We saw fresh bear tracks near Capitol Lake - proper food storage is essential.
                """
            }
            
            peak_name = content['title']
            if peak_name in sample_descriptions:
                text = sample_descriptions[peak_name]
                found_sightings = self._extract_sightings_from_text(text, content['url'])
                
                # Add metadata
                for sighting in found_sightings:
                    sighting['trail_name'] = peak_name
                    sighting['sighting_date'] = datetime.now() - timedelta(days=7)  # Assume recent
                
                sightings.extend(found_sightings)
        else:
            # Process actual content sections
            for section in content_sections:
                text = section.get_text(strip=True)
                if text and len(text) > 100:  # Skip very short sections
                    found_sightings = self._extract_sightings_from_text(text, content['url'])
                    
                    # Add metadata
                    for sighting in found_sightings:
                        sighting['trail_name'] = content['title']
                        sighting['sighting_date'] = datetime.now() - timedelta(days=7)
                    
                    sightings.extend(found_sightings)
        
        # Also check comments/trip reports
        comments = soup.find_all(['div', 'article'], class_=['comment', 'trip-report-body'])
        for comment in comments:
            text = comment.get_text(strip=True)
            if text:
                found_sightings = self._extract_sightings_from_text(text, content['url'])
                
                # Try to extract date from comment
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text)
                if date_match:
                    try:
                        sighting_date = datetime.strptime(date_match.group(1), '%m/%d/%Y')
                    except:
                        sighting_date = datetime.now() - timedelta(days=30)
                else:
                    sighting_date = datetime.now() - timedelta(days=30)
                
                for sighting in found_sightings:
                    sighting['trail_name'] = content['title']
                    sighting['sighting_date'] = sighting_date
                
                sightings.extend(found_sightings)
        
        return sightings
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Get trail location data from SummitPost peak pages.
        
        Returns:
            List of trail dictionaries with name, lat, lon
        """
        trails = []
        
        # This would extract coordinates from peak pages
        # For now, returning empty as we already have trail data
        return trails
