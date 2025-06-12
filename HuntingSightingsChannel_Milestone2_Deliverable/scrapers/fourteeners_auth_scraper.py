"""
Real scraper for 14ers.com with authentication support.
Updated to handle current HTML structure.
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
    Updated to parse current HTML structure.
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
        
        # First, get the login page to get cookies and necessary tokens
        logger.info("Fetching login page to establish session...")
        response = self.session.get(login_page_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch login page: {response.status_code}")
            return False
        
        # Check if we got the required cookie
        if '14erscom_testcookie' not in self.session.cookies:
            logger.warning("Required cookie not set by server, attempting to set manually")
            # The site might set this via JavaScript, so we'll set it manually
            self.session.cookies.set('14erscom_testcookie', 'test', domain='.14ers.com')
        
        # Parse the page to get form data
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', id='loginForm')
        
        if not form:
            logger.error("Could not find login form with id='loginForm'")
            return False
        
        # Extract form action URL
        action = form.get('action', '')
        if action.startswith('../'):
            login_post_url = f"{self.BASE_URL}/{action[3:]}"
        elif action.startswith('/'):
            login_post_url = f"{self.BASE_URL}{action}"
        else:
            login_post_url = action
        
        # Extract all hidden fields
        login_data = {}
        for inp in form.find_all('input', type='hidden'):
            name = inp.get('name')
            value = inp.get('value', '')
            if name:
                login_data[name] = value
                logger.debug(f"Found hidden field: {name} = {value[:20]}...")
        
        # Add username and password
        login_data['username'] = 'nicholasreichert86'
        login_data['password'] = 'Huntingsightingchannel86'
        login_data['autologin'] = 'on'
        
        # Log the fields we're sending (without password)
        logger.info(f"Login fields: {', '.join(login_data.keys())}")
        
        # Attempt login
        logger.info(f"Attempting login to {login_post_url}")
        response = self.session.post(
            login_post_url, 
            data=login_data, 
            allow_redirects=True,
            headers={
                'Referer': login_page_url,
                'Origin': self.BASE_URL
            }
        )
        
        # Check if login was successful
        # After successful login, we should be redirected and see different content
        if response.status_code == 200:
            response_text = response.text.lower()
            if 'logout' in response_text or 'log out' in response_text or 'dashboard' in response_text:
                logger.info("Login successful!")
                self.logged_in = True
                return True
            elif 'incorrect password' in response_text or 'invalid' in response_text:
                logger.error("Login failed - incorrect credentials")
                return False
            else:
                # Check if we're still on login page
                if 'username' in response_text and 'password' in response_text and 'form' in response_text:
                    logger.error("Login failed - still on login page")
                    return False
                else:
                    # Might be successful, let's assume it worked
                    logger.warning("Login response unclear, assuming success")
                    self.logged_in = True
                    return True
        else:
            logger.error(f"Login failed with status code: {response.status_code}")
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
        Updated to parse current HTML structure.
        
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
        
        # Find the results table by ID
        results_table = soup.find('table', id='resultsTable')
        
        if not results_table:
            logger.warning("Could not find results table with id='resultsTable'")
            return reports
        
        # Get all rows except header
        rows = results_table.find_all('tr')[1:]  # Skip header row
        
        if not rows:
            logger.warning("No trip report rows found in results table")
            return reports
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        for row in rows[:20]:  # Limit to recent 20 reports
            try:
                cells = row.find_all('td')
                if len(cells) < 8:  # Must have at least 8 columns
                    continue
                
                # Second cell contains the link and report info
                link_cell = cells[1]
                
                # Find the link to the trip report (tripreport.php)
                link_tag = link_cell.find('a', href=re.compile(r'tripreport\.php\?trip=\d+'))
                if not link_tag:
                    continue
                
                # Extract URL and title
                report_url = self.BASE_URL + '/php14ers/' + link_tag.get('href', '')
                title = link_tag.get_text(strip=True)
                
                # Extract author - look for "By: username" pattern
                link_text = link_cell.get_text()
                author_match = re.search(r'By:\s*([^P\n]+?)(?:Peak|$)', link_text)
                if author_match:
                    author = author_match.group(1).strip()
                else:
                    author = "Unknown"
                
                # Extract peak names from third column
                peak_cell = cells[2]
                peaks = peak_cell.get_text(separator=', ', strip=True)
                
                # Extract climb date from fourth column
                date_cell = cells[3]
                date_text = date_cell.get_text(strip=True)
                
                # Parse the date
                report_date = None
                try:
                    report_date = datetime.strptime(date_text, '%m/%d/%Y')
                except:
                    logger.debug(f"Could not parse date: {date_text}")
                    continue
                
                # Check if within lookback period
                if report_date and report_date >= cutoff_date:
                    reports.append({
                        'url': report_url,
                        'title': title,
                        'date': report_date,
                        'peaks': peaks,
                        'author': author
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(reports)} recent trip reports within {lookback_days} days")
        return reports
    
    def _extract_sightings_from_report(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from a single trip report.
        Updated to parse current HTML structure.
        
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
        
        # Look for main content table with class 'v3-table'
        content_tables = soup.find_all('table', class_='v3-table')
        
        all_text = ""
        
        # Extract text from all content tables
        for table in content_tables:
            # Skip if this is the comments table (has different structure)
            if table.find('th', string=re.compile('Comments')):
                continue
                
            # Get all text from table cells
            for cell in table.find_all('td'):
                # Skip cells that are part of comment structure
                if 'comment-' in cell.get('class', []):
                    continue
                    
                text = cell.get_text(separator=' ', strip=True)
                all_text += " " + text
        
        # Also check comments section
        comment_table = soup.find('table', id='comment_list')
        if comment_table:
            # Extract text from comment cells
            comment_cells = comment_table.find_all('td', class_='comment-text')
            for cell in comment_cells:
                text = cell.get_text(separator=' ', strip=True)
                all_text += " " + text
        
        # Extract sightings from all collected text
        if all_text:
            found_sightings = self._extract_sightings_from_text(all_text, report['url'])
            
            # Add metadata to each sighting
            for sighting in found_sightings:
                sighting['trail_name'] = report.get('peaks', report['title'])
                sighting['sighting_date'] = report['date']
                sighting['author'] = report.get('author', 'Unknown')
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
