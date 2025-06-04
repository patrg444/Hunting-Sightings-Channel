"""
Real scraper for 14ers.com trip reports to extract wildlife sightings.
This version actually scrapes the website.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
import time

from .base import BaseScraper


class FourteenersRealScraper(BaseScraper):
    """
    Real scraper for 14ers.com trip reports and peak pages.
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
        
        # Get recent trip reports from the trip reports page
        trip_reports = self._get_recent_trip_reports_real(lookback_days)
        
        # Extract sightings from each report
        for report in trip_reports:
            sightings = self._extract_sightings_from_report(report)
            all_sightings.extend(sightings)
        
        logger.info(f"Found {len(all_sightings)} total sightings from 14ers.com")
        return all_sightings
    
    def _get_recent_trip_reports_real(self, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Get links to recent trip reports from the actual website.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            List of trip report metadata
        """
        reports = []
        
        # The actual trip reports page
        reports_url = f"{self.BASE_URL}/php14ers/tripmain.php"
        
        logger.info(f"Fetching trip reports from {reports_url}")
        response = self._make_request(reports_url)
        
        if not response:
            logger.error("Failed to fetch trip reports page")
            return reports
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find trip report links - look for all tables
        tables = soup.find_all('table')
        
        # Look for the reports table (usually has links to tripshow.php)
        report_rows = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                # Check if this row has a link to tripshow.php
                link = row.find('a', href=lambda x: x and 'tripshow.php' in x if x else False)
                if link:
                    report_rows.append(row)
        
        if not report_rows:
            logger.warning("Could not find trip report rows")
            return reports
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        for row in report_rows[:20]:  # Limit to recent 20 reports
            try:
                # Find the link to the trip report
                link_tag = row.find('a', href=lambda x: x and 'tripshow.php' in x if x else False)
                if not link_tag:
                    continue
                
                # Extract URL and title
                report_url = self.BASE_URL + '/php14ers/' + link_tag.get('href', '')
                title = link_tag.get_text(strip=True)
                
                # Look for date in the row - it's typically in format M/D/YYYY
                cells = row.find_all('td')
                report_date = None
                
                for cell in cells:
                    text = cell.get_text(strip=True)
                    # Try to parse as date
                    if '/' in text and len(text) < 15:
                        try:
                            report_date = datetime.strptime(text, '%m/%d/%Y')
                            break
                        except:
                            try:
                                # Try with 2-digit year
                                report_date = datetime.strptime(text, '%m/%d/%y')
                                break
                            except:
                                pass
                
                if report_date and report_date >= cutoff_date:
                    reports.append({
                        'url': report_url,
                        'title': title,
                        'date': report_date
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(reports)} recent trip reports")
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
        logger.info(f"Fetching report: {report['title']}")
        response = self._make_request(report['url'])
        if not response:
            return sightings
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for trip report content
        # 14ers.com trip reports are typically in div with class 'wide'
        content_div = soup.find('div', {'class': 'wide'})
        
        if content_div:
            # Get all text content
            text = content_div.get_text(separator=' ', strip=True)
            
            # Extract sightings
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
        
        # Could scrape the peaks list page
        # For now, returning empty as we already have trail data
        return trails
