"""
Browser-based scraper for SummitPost.org using Playwright.
This scraper uses a real browser to bypass anti-scraping measures.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")

from .base import BaseScraper


class SummitPostPlaywrightScraper(BaseScraper):
    """
    Browser-based scraper for SummitPost.org using Playwright.
    Fetches real data by simulating a real browser.
    """
    
    BASE_URL = "https://www.summitpost.org"
    
    def __init__(self):
        super().__init__(source_name="summitpost.org", rate_limit=2.0)
        self.browser = None
        self.page = None
        self.playwright = None
        
    def _init_browser(self):
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chromium")
        
        logger.info("Initializing Playwright browser...")
        self.playwright = sync_playwright().start()
        
        # Launch browser with options to look more human-like
        self.browser = self.playwright.chromium.launch(
            headless=True,  # Set to False to see the browser
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create a new page with realistic viewport
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = context.new_page()
        
        # Add human-like behavior
        self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        
    def _close_browser(self):
        """Clean up browser resources."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape recent content from SummitPost using a real browser.
        
        Args:
            lookback_days: Number of days to look back for content
            
        Returns:
            List of wildlife sightings
        """
        all_sightings = []
        
        try:
            # Initialize browser
            self._init_browser()
            
            # Get recent trip reports
            trip_reports = self._get_recent_trip_reports_browser()
            
            # Extract sightings from each report
            for report in trip_reports[:3]:  # Limit to 3 for demo
                sightings = self._extract_sightings_from_report_browser(report)
                all_sightings.extend(sightings)
            
            # Also get popular Colorado peak pages
            peak_pages = self._get_colorado_peaks()
            for peak in peak_pages[:2]:  # Limit to 2 for demo
                sightings = self._extract_sightings_from_peak_page_browser(peak)
                all_sightings.extend(sightings)
            
            logger.info(f"Found {len(all_sightings)} total sightings from SummitPost")
            
        finally:
            # Always close browser
            self._close_browser()
        
        return all_sightings
    
    def _get_recent_trip_reports_browser(self) -> List[Dict[str, Any]]:
        """
        Get recent trip reports using browser navigation.
        
        Returns:
            List of trip report metadata
        """
        reports = []
        
        # Navigate to Colorado trip reports
        url = f"{self.BASE_URL}/object_list.php?object_type=5&state_province_1=Colorado"
        logger.info(f"Navigating to trip reports: {url}")
        
        try:
            # Navigate and wait for content
            self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for the main content to load
            self.page.wait_for_selector('table', timeout=10000)
            
            # Extract trip report links
            report_elements = self.page.query_selector_all('a[href*="/trip-report/"]')
            
            for element in report_elements[:10]:  # Limit to 10 recent
                try:
                    title = element.inner_text()
                    href = element.get_attribute('href')
                    
                    if href and not href.startswith('http'):
                        href = self.BASE_URL + href
                    
                    reports.append({
                        'title': title,
                        'url': href,
                        'type': 'trip_report'
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing report element: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to get trip reports: {e}")
            # Try alternative approach - search for Colorado content
            try:
                search_url = f"{self.BASE_URL}/search/results.php?query=Colorado+trip+report"
                self.page.goto(search_url, wait_until='networkidle', timeout=30000)
                
                # Find search results
                result_links = self.page.query_selector_all('a.results-title')
                for link in result_links[:5]:
                    title = link.inner_text()
                    href = link.get_attribute('href')
                    if href and 'trip-report' in href:
                        reports.append({
                            'title': title,
                            'url': self.BASE_URL + href if not href.startswith('http') else href,
                            'type': 'trip_report'
                        })
                        
            except Exception as e2:
                logger.error(f"Alternative search also failed: {e2}")
        
        logger.info(f"Found {len(reports)} trip reports")
        return reports
    
    def _extract_sightings_from_report_browser(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from a trip report using browser.
        
        Args:
            report: Trip report metadata
            
        Returns:
            List of sightings found in this report
        """
        sightings = []
        
        try:
            # Navigate to report
            logger.info(f"Navigating to report: {report['title']}")
            self.page.goto(report['url'], wait_until='networkidle', timeout=30000)
            
            # Wait for content
            self.page.wait_for_selector('body', timeout=5000)
            
            # Extract all text content
            content_elements = self.page.query_selector_all('div, td, p')
            all_text = ""
            
            for element in content_elements:
                try:
                    text = element.inner_text()
                    if text and len(text) > 50:
                        all_text += " " + text
                except:
                    continue
            
            # Extract sightings from text
            if all_text:
                found_sightings = self._extract_sightings_from_text(all_text, report['url'])
                
                for sighting in found_sightings:
                    sighting['report_title'] = report['title']
                    sighting['sighting_date'] = datetime.now() - timedelta(days=7)
                
                sightings.extend(found_sightings)
                
                if sightings:
                    logger.info(f"Found {len(sightings)} sightings in report: {report['title']}")
                    
        except Exception as e:
            logger.error(f"Error extracting from report {report['url']}: {e}")
        
        return sightings
    
    def _get_colorado_peaks(self) -> List[Dict[str, Any]]:
        """Get popular Colorado peak pages."""
        return [
            {'name': 'Longs Peak', 'url': f"{self.BASE_URL}/longs-peak/150329", 'type': 'peak_page'},
            {'name': 'Mount Elbert', 'url': f"{self.BASE_URL}/mount-elbert/150325", 'type': 'peak_page'},
            {'name': 'Pikes Peak', 'url': f"{self.BASE_URL}/pikes-peak/150301", 'type': 'peak_page'},
            {'name': 'Mount Evans', 'url': f"{self.BASE_URL}/mount-evans/150379", 'type': 'peak_page'}
        ]
    
    def _extract_sightings_from_peak_page_browser(self, peak: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract wildlife sightings from a peak page using browser.
        
        Args:
            peak: Peak page metadata
            
        Returns:
            List of sightings found on this peak page
        """
        sightings = []
        
        try:
            # Navigate to peak page
            logger.info(f"Navigating to peak page: {peak['name']}")
            self.page.goto(peak['url'], wait_until='networkidle', timeout=30000)
            
            # Look for route descriptions and recent comments
            route_sections = self.page.query_selector_all('div.route-body, div.description')
            comments = self.page.query_selector_all('div.comment-body, div.message-body')
            
            # Extract text from routes
            for section in route_sections:
                try:
                    text = section.inner_text()
                    if text and len(text) > 100:
                        found_sightings = self._extract_sightings_from_text(text, peak['url'])
                        
                        for sighting in found_sightings:
                            sighting['trail_name'] = peak['name']
                            sighting['sighting_date'] = datetime.now() - timedelta(days=30)
                        
                        sightings.extend(found_sightings)
                except:
                    continue
            
            # Extract text from recent comments
            for comment in comments[:5]:  # Recent comments only
                try:
                    text = comment.inner_text()
                    if text and len(text) > 50:
                        found_sightings = self._extract_sightings_from_text(text, peak['url'])
                        
                        for sighting in found_sightings:
                            sighting['trail_name'] = peak['name']
                            sighting['sighting_date'] = datetime.now() - timedelta(days=14)
                            sighting['is_comment'] = True
                        
                        sightings.extend(found_sightings)
                except:
                    continue
            
            if sightings:
                logger.info(f"Found {len(sightings)} sightings on peak page: {peak['name']}")
                
        except Exception as e:
            logger.error(f"Error extracting from peak page {peak['url']}: {e}")
        
        return sightings
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """Get trail location data from SummitPost peak pages."""
        return []
