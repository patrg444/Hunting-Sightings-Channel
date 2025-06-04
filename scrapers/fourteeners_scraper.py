"""
Scraper for 14ers.com trip reports to extract wildlife sightings.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseScraper


class FourteenersScraper(BaseScraper):
    """
    Scraper for 14ers.com trip reports and peak pages.
    """
    
    BASE_URL = "https://www.14ers.com"
    
    def __init__(self):
        super().__init__(source_name="14ers.com", rate_limit=1.0)
        
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape recent trip reports from 14ers.com.
        
        Args:
            lookback_days: Number of days to look back for reports
            
        Returns:
            List of wildlife sightings
        """
        all_sightings = []
        
        # Get recent trip reports
        trip_reports = self._get_recent_trip_reports(lookback_days)
        
        # Extract sightings from each report
        for report in trip_reports:
            sightings = self._extract_sightings_from_report(report)
            all_sightings.extend(sightings)
        
        logger.info(f"Found {len(all_sightings)} total sightings from 14ers.com")
        return all_sightings
    
    def _get_recent_trip_reports(self, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Get links to recent trip reports.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            List of trip report metadata
        """
        reports = []
        
        # 14ers.com trip report index URL
        # Note: In practice, we'd parse the actual trip report pages
        # For now, using sample URLs
        sample_report_urls = [
            "/route.php?route=elbe1&peak=Mt.+Elbert",
            "/route.php?route=evan1&peak=Mt.+Evans",
            "/route.php?route=gray1&peak=Grays+Peak"
        ]
        
        # For MVP, we'll simulate trip reports with sample content
        for url in sample_report_urls:
            reports.append({
                'url': self.BASE_URL + url,
                'title': url.split('peak=')[1].replace('+', ' '),
                'date': datetime.now() - timedelta(days=1)
            })
        
        return reports
    
    def _extract_sightings_from_report(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from a single trip report.
        
        Args:
            report: Trip report metadata
            
        Returns:
            List of sightings found in this report
        """
        sightings = []
        
        # Fetch the report page
        response = self._make_request(report['url'])
        if not response:
            return sightings
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for trip report content
        # Note: Actual selectors would need to be determined by inspecting 14ers.com
        content_areas = soup.find_all(['div', 'p'], class_=['trip-report', 'route-description', 'content'])
        
        # For MVP simulation, let's add some sample content
        if not content_areas:
            # Simulate some trip report content
            sample_contents = {
                "Mt. Elbert": "Started early at 4am from the trailhead. About halfway up we spotted a small herd of elk grazing near treeline. Beautiful morning!",
                "Mt. Evans": "Drive up was easy. Saw several mountain goats near the summit parking area. Also saw a black bear crossing the road on the way down.",
                "Grays Peak": "Great hike! Encountered a group of bighorn sheep on the traverse between Grays and Torreys. They didn't seem bothered by hikers."
            }
            
            peak_name = report['title']
            if peak_name in sample_contents:
                text = sample_contents[peak_name]
                found_sightings = self._extract_sightings_from_text(text, report['url'])
                
                # Add metadata
                for sighting in found_sightings:
                    sighting['trail_name'] = peak_name
                    sighting['sighting_date'] = report['date']
                
                sightings.extend(found_sightings)
        else:
            # Process actual content
            for content in content_areas:
                text = content.get_text(strip=True)
                if text:
                    found_sightings = self._extract_sightings_from_text(text, report['url'])
                    
                    # Add metadata
                    for sighting in found_sightings:
                        sighting['trail_name'] = report['title']
                        sighting['sighting_date'] = report['date']
                    
                    sightings.extend(found_sightings)
        
        return sightings
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Get trail location data from 14ers.com peak pages.
        
        Returns:
            List of trail dictionaries with name, lat, lon
        """
        trails = []
        
        # This would scrape the peak list page
        # For now, returning empty as we already have trail data
        return trails
