"""
Real scraper for 14ers.com trip reports to extract wildlife sightings.
This version actually scrapes the website with updated parsing logic.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
import time

from .base import BaseScraper
from .llm_validator import LLMValidator


class FourteenersRealScraper(BaseScraper):
    """
    Real scraper for 14ers.com trip reports and peak pages.
    Updated to handle current HTML structure and LLM validation.
    """
    
    BASE_URL = "https://www.14ers.com"
    
    def __init__(self):
        super().__init__(source_name="14ers.com", rate_limit=1.0)
        self.llm_validator = LLMValidator()
        
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
        Updated to parse current HTML structure.
        
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
                
                # Extract peak names from third column (class="hide-10")
                peak_cell = cells[2]
                peaks = peak_cell.get_text(separator=', ', strip=True)
                
                # Extract climb date from fourth column (class="hide-7")
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
        response = self._make_request(report['url'])
        if not response:
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
                sighting['location_name'] = report.get('peaks', report['title'])
                sighting['sighting_date'] = report['date']
                sighting['author'] = report.get('author', 'Unknown')
                sighting['report_title'] = report['title']
            
            sightings.extend(found_sightings)
        
        if sightings:
            logger.info(f"Found {len(sightings)} sightings in report: {report['title']}")
        
        return sightings
    
    def _extract_sightings_from_text(self, text: str, url: str) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from text using LLM validation.
        Overrides base class to use advanced extraction.
        
        Args:
            text: Text to search for sightings
            url: Source URL for attribution
            
        Returns:
            List of sighting dictionaries with LLM validation
        """
        sightings = []
        
        # First find potential mentions
        potential_mentions = self._extract_potential_wildlife_mentions(text, url)
        
        if not potential_mentions:
            return sightings
        
        # Use LLM to validate each potential mention
        for mention in potential_mentions:
            # Extract the peak name from URL for context
            peak_name = "Colorado 14er"
            if '/route.php' in url:
                try:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(url)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'peak' in params:
                        peak_name = params['peak'][0].replace('+', ' ')
                except:
                    pass
            
            # Enhanced context for LLM
            enhanced_text = f"Trip report from {peak_name}: {mention['full_text']}"
            
            # Use LLM validator
            analysis = self.llm_validator.analyze_full_text_for_sighting(
                enhanced_text,
                mention['species_mentioned'],
                '14ers.com'  # Pass source context
            )
            
            if analysis:
                # Create sighting with LLM validation data
                sighting = {
                    'species': analysis['species'],
                    'raw_text': mention['raw_text'],
                    'keyword_matched': mention['keyword_matched'],
                    'source_url': url,
                    'source_type': '14ers.com',
                    'extracted_at': datetime.now().isoformat(),
                    
                    # LLM validation fields
                    'confidence': analysis.get('confidence', 80),
                    'llm_validated': True,
                    'location_confidence_radius': analysis.get('location_confidence_radius'),
                    
                    # Location data from LLM
                    'location_details': analysis.get('location_details', {})
                }
                
                # Add any extracted location fields
                location_fields = ['gmu_number', 'county', 'location_name', 'coordinates', 'elevation', 'location_description']
                for field in location_fields:
                    if field in analysis:
                        sighting[field] = analysis[field]
                
                sightings.append(sighting)
                logger.debug(f"LLM validated sighting: {analysis['species']} at {peak_name}")
        
        return sightings
    
    def _extract_potential_wildlife_mentions(self, text: str, source_url: str) -> List[Dict[str, Any]]:
        """Helper method to extract potential mentions for LLM validation."""
        mentions = []
        text_lower = text.lower()
        
        for species, keywords in self.game_species.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Find context around keyword
                    index = text_lower.find(keyword.lower())
                    start = max(0, index - 100)
                    end = min(len(text), index + len(keyword) + 100)
                    
                    mentions.append({
                        'species_mentioned': species,
                        'keyword_matched': keyword,
                        'source_url': source_url,
                        'full_text': text[start:end],
                        'raw_text': text[start:end]
                    })
                    break  # Only need one keyword match per species
        
        return mentions
    
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
