# Milestone 2: Core Scrapers Deliverable

## Overview
This package contains the complete implementation of three core web scrapers for the Wildlife Sightings Channel project. All scrapers work with real data sources and have been tested in production.

## What's Included

### 1. Scrapers (Real Data Only)
- **Reddit Scraper** (`scrapers/reddit_scraper.py`)
  - Uses Reddit API with OAuth authentication
  - Monitors 9 hunting/outdoor subreddits
  - Includes LLM validation with OpenAI
  - 90%+ cache efficiency

- **14ers.com Scraper** (`scrapers/fourteeners_scraper_real.py`)
  - HTML scraping of trip reports
  - Login capability included
  - Extracts wildlife mentions from recent reports

- **SummitPost Scraper** (`scrapers/summitpost_playwright_scraper.py`)
  - Uses Playwright browser automation
  - Bypasses anti-scraping measures
  - Searches for wildlife mentions on peak pages

### 2. CLI Tools
- `scripts/sightings_cli.py` - Query sightings by GMU and date
- `scripts/run_scrapers.py` - Run all scrapers and save results

### 3. Test Scripts
- `scripts/test_scrapers_demo.py` - Full demonstration of all scrapers
- `scripts/test_reddit.py` - Test Reddit scraper individually
- `scripts/search_wildlife_reports.py` - Test 14ers scraper
- `scripts/test_summitpost_playwright.py` - Test SummitPost browser scraper

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Playwright (for SummitPost)
```bash
pip install playwright
playwright install chromium
```

### 3. Configure Environment
```bash
# Option A: Use provided Reddit credentials
cp .env.client .env
# Only need to add your OpenAI API key

# Option B: Use your own credentials
cp .env.example .env
# Edit .env with all your credentials
```

**Note: .env.client includes working Reddit API credentials created for this project**

### 4. Test Individual Scrapers
```bash
# Test Reddit scraper
python scripts/test_reddit.py

# Test 14ers scraper
python scripts/search_wildlife_reports.py

# Test SummitPost scraper
python scripts/test_summitpost_playwright.py
```

### 5. Run Full Demo
```bash
python scripts/test_scrapers_demo.py
```

### 6. Run All Scrapers
```bash
python scripts/run_scrapers.py
```

## Output
- Sightings are saved to JSON format
- Can be filtered by GMU, date, species
- Includes location data (GMU, elevation, coordinates)

## Key Features Demonstrated
- Multiple authentication methods (OAuth, session-based)
- Browser automation for protected sites
- Keyword and location extraction
- Structured data output
- Rate limiting and caching
- Modular, extensible design
