#!/usr/bin/env python3
"""
Script to scrape and analyze an individual 14ers.com trip report.
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from loguru import logger
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.fourteeners_scraper_real import FourteenersRealScraper


def analyze_trip_report(url: str):
    """Analyze a single trip report in detail."""
    logger.info(f"Analyzing trip report: {url}")
    
    # Create scraper instance
    scraper = FourteenersRealScraper()
    
    # Fetch the report
    response = scraper._make_request(url)
    if not response:
        logger.error("Failed to fetch report")
        return
    
    # Save the HTML for inspection
    with open('trip_report.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    logger.info("Saved HTML to trip_report.html")
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all content tables
    logger.info("\n=== ANALYZING CONTENT STRUCTURE ===")
    
    # Look for main content tables
    content_tables = soup.find_all('table', class_='v3-table')
    logger.info(f"Found {len(content_tables)} tables with class 'v3-table'")
    
    # Extract text from each table
    all_text = ""
    for i, table in enumerate(content_tables):
        logger.info(f"\nTable {i+1}:")
        
        # Check if it's a comments table
        if table.find('th', string=lambda x: x and 'Comments' in x):
            logger.info("  - This is a comments table (skipping)")
            continue
        
        # Extract text from cells
        text_content = ""
        cells = table.find_all('td')
        for cell in cells:
            # Skip comment-related cells
            if 'comment-' in str(cell.get('class', [])):
                continue
            
            cell_text = cell.get_text(separator=' ', strip=True)
            if len(cell_text) > 50:  # Only show substantial content
                text_content += cell_text + " "
        
        if text_content:
            logger.info(f"  - Content preview: {text_content[:200]}...")
            all_text += " " + text_content
    
    # Check for comments section
    logger.info("\n=== CHECKING COMMENTS ===")
    comment_table = soup.find('table', id='comment_list')
    if comment_table:
        logger.info("Found comment table")
        comment_cells = comment_table.find_all('td', class_='comment-text')
        logger.info(f"Found {len(comment_cells)} comments")
        
        for i, cell in enumerate(comment_cells[:3]):  # Show first 3 comments
            comment_text = cell.get_text(separator=' ', strip=True)
            logger.info(f"Comment {i+1}: {comment_text[:100]}...")
            all_text += " " + comment_text
    else:
        logger.info("No comment table found")
    
    # Extract wildlife sightings
    logger.info("\n=== EXTRACTING WILDLIFE SIGHTINGS ===")
    
    # Create a mock report object
    report = {
        'url': url,
        'title': 'Test Report',
        'date': datetime.now(),
        'peaks': 'Unknown Peak',
        'author': 'Test Author'
    }
    
    # Use the scraper's extraction method
    sightings = scraper._extract_sightings_from_report(report)
    
    if sightings:
        logger.success(f"Found {len(sightings)} wildlife sightings!")
        
        for i, sighting in enumerate(sightings):
            logger.info(f"\nSighting {i+1}:")
            logger.info(f"  Species: {sighting['species']}")
            logger.info(f"  Context: {sighting['raw_text']}")
            logger.info(f"  Keyword: {sighting['keyword_matched']}")
            logger.info(f"  Date: {sighting['sighting_date']}")
    else:
        logger.warning("No wildlife sightings found")
    
    # Show all text extracted
    logger.info(f"\n=== TOTAL TEXT EXTRACTED ===")
    logger.info(f"Total characters extracted: {len(all_text)}")
    
    # Search for wildlife keywords manually
    logger.info("\n=== MANUAL WILDLIFE KEYWORD SEARCH ===")
    wildlife_keywords = ['elk', 'deer', 'bear', 'moose', 'bighorn', 'sheep', 'goat', 'mountain goat', 'pronghorn', 'antelope']
    
    for keyword in wildlife_keywords:
        count = all_text.lower().count(keyword.lower())
        if count > 0:
            logger.info(f"'{keyword}' appears {count} times")
            
            # Show context for first occurrence
            index = all_text.lower().find(keyword.lower())
            if index != -1:
                start = max(0, index - 50)
                end = min(len(all_text), index + len(keyword) + 50)
                context = all_text[start:end]
                logger.info(f"  Context: ...{context}...")


def main():
    """Main function to run the analysis."""
    # We'll use one of the trip reports found earlier
    sample_urls = [
        "https://www.14ers.com/php14ers/tripreport.php?trip=23045",  # Angel Knob - North Couloirs
        "https://www.14ers.com/php14ers/tripreport.php?trip=23043",  # EngRoBarParnasty loop
        "https://www.14ers.com/php14ers/tripreport.php?trip=23041",  # Slushy day at Mount Bierstadt
    ]
    
    # Let's analyze the first one
    if len(sys.argv) > 1:
        # Allow custom URL from command line
        url = sys.argv[1]
    else:
        url = sample_urls[0]
    
    analyze_trip_report(url)


if __name__ == "__main__":
    main()
