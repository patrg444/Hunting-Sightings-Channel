"""
Real scraper for 14ers.com with authentication support.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
import requests

from .base import BaseScraper


class FourteenersAuthScraper(BaseScraper):
    """
    Authenticated scraper for 14ers.com trip reports.
    """
    
    BASE_URL = "https://www.14ers.com"
    
    def __init__(self):
        super().__init__(source_name="14ers.com", rate_limit=1.0)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logged_in = False
        
    def _login(self) -> bool:
        """
        Login to 14ers.com using provided credentials.
        
        Returns:
            True if login successful, False otherwise
        """
        login_page_url = f"{self.BASE_URL}/php14ers/loginviaforum.php"
        
        # First, get the login page to get any necessary tokens
        logger.info("Fetching login page...")
        response = self.session.get(login_page_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch login page: {response.status_code}")
            return False
        
        # Parse the page to get form data
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        
        if not form:
            logger.error("Could not find login form")
            return False
        
        # Extract form action URL
        action = form.get('action', '')
        if action.startswith('../'):
            login_post_url = f"{self.BASE_URL}/{action[3:]}"
        else:
            login_post_url = action
        
        # Extract all hidden fields
        login_data = {}
        for inp in form.find_all('input', type='hidden'):
            name = inp.get('name')
            value = inp.get('value', '')
            if name:
                login_data[name] = value
        
        # Add username and password
        login_data['username'] = 'nicholasreichert86'
        login_data['password'] = 'Huntingsightingchannel86'
        login_data['autologin'] = 'on'
        
        # Attempt login
        logger.info(f"Attempting login to {login_post_url}")
        response = self.session.post(login_post_url, data=login_data, allow_redirects=True)
        
        # Check if login was successful
        # After successful login, we should be redirected and see different content
        if response.status_code == 200 and ('logout' in response.text.lower() or 'Log out' in response.text):
            logger.info("Login successful!")
            self.logged_in = True
            return True
        else:
            logger.error("Login failed")
            return False
        
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape recent trip reports from 14ers.com.
        
        Args:
            lookback_days: Number of days to look back for reports
            
        Returns:
            List of wildlife sightings
        """
        # Login first if not already logged in
        if not self.logged_in:
            if not self._login():
                logger.error("Failed to login to 14ers.com")
                return []
        
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
        Get links to recent trip reports from the website.
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            List of trip report metadata
        """
        reports = []
        
        # The trip reports page
        reports_url = f"{self.BASE_URL}/php14ers/tripmain.php"
        
        logger.info(f"Fetching trip reports from {reports_url}")
        response = self.session.get(reports_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch trip reports page: {response.status_code}")
            return reports
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # The main table has report rows
        # Look for table rows containing trip report links
        report_rows = soup.find_all('tr')
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        for row in report_rows:
            try:
                # Find link to tripshow.php
                link = row.find('a', href=lambda x: x and 'tripshow.php' in x if x else False)
                if not link:
                    continue
                
                # Extract report details
                report_url = self.BASE_URL + '/php14ers/' + link.get('href', '')
                title = link.get_text(strip=True)
                
                # Find date - look for M/D/YYYY pattern in cells
                cells = row.find_all('td')
                report_date = None
                
                for cell in cells:
                    text = cell.get_text(strip=True)
                    # Match date pattern M/D/YYYY
                    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
                    if date_match:
                        try:
                            report_date = datetime.strptime(date_match.group(0), '%m/%d/%Y')
                            break
                        except:
                            pass
                
                if report_date and report_date >= cutoff_date:
                    # Extract peak names from the row
                    peak_info = ""
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if any(peak in cell_text for peak in ['Peak', 'Mountain', 'Mt.']):
                            peak_info = cell_text
                            break
                    
                    reports.append({
                        'url': report_url,
                        'title': title,
                        'date': report_date,
                        'peaks': peak_info
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(reports)} recent trip reports within {lookback_days} days")
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
        response = self.session.get(report['url'])
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch report {report['url']}: {response.status_code}")
            return sightings
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trip report content is usually in a main content area
        # Look for the main text content
        content_areas = soup.find_all(['div', 'td'], class_=['content', 'wide', 'postbody'])
        
        # If no specific content areas found, get all text from body
        if not content_areas:
            content_areas = [soup.body] if soup.body else []
        
        for content in content_areas:
            # Get text content
            text = content.get_text(separator=' ', strip=True)
            
            # Extract sightings
            found_sightings = self._extract_sightings_from_text(text, report['url'])
            
            # Add metadata
            for sighting in found_sightings:
                sighting['trail_name'] = report.get('peaks', report['title'])
                sighting['sighting_date'] = report['date']
                sighting['report_title'] = report['title']
            
            sightings.extend(found_sightings)
        
        if sightings:
            logger.info(f"Found {len(sightings)} sightings in report: {report['title']}")
        
        return sightings
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Get trail location data from 14ers.com peak pages.
        
        Returns:
            List of trail dictionaries with name, lat, lon
        """
        return []
