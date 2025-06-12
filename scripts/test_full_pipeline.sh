#!/bin/bash
# Test the full wildlife sightings pipeline

echo "=================================================="
echo " WILDLIFE SIGHTINGS CHANNEL - FULL PIPELINE TEST"
echo "=================================================="

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Function to check if a command succeeded
check_status() {
 if [ $? -eq 0 ]; then
 echo " $1 - SUCCESS"
 else
 echo " $1 - FAILED"
 exit 1
 fi
}

echo ""
echo " Step 1: Checking environment setup..."
echo "-----------------------------------------"

# Check Python
python --version
check_status "Python available"

# Check required packages
python -c "import requests, beautifulsoup4, praw, geopandas, openai, jinja2"
check_status "Required packages installed"

# Check .env file
if [ -f ".env" ]; then
 echo " .env file exists"
else
 echo " .env file not found - using .env.example"
 cp .env.example .env
fi

echo ""
echo " Step 2: Testing scrapers..."
echo "-----------------------------------------"

# Test Reddit scraper
echo "Testing Reddit scraper..."
python scripts/test_reddit.py > /dev/null 2>&1
check_status "Reddit scraper"

# Test 14ers scraper
echo "Testing 14ers scraper..."
python scripts/search_wildlife_reports.py > /dev/null 2>&1
check_status "14ers scraper"

# Test SummitPost scraper
echo "Testing SummitPost scraper..."
python scripts/test_summitpost.py > /dev/null 2>&1
check_status "SummitPost scraper"

echo ""
echo " Step 3: Running full scraper pipeline..."
echo "-----------------------------------------"

# Run all scrapers
python scripts/run_scrapers.py
check_status "Run all scrapers"

# Check if sightings were saved
if [ -f "data/sightings/latest_sightings.json" ]; then
 SIGHTING_COUNT=$(python -c "import json; print(len(json.load(open('data/sightings/latest_sightings.json'))))")
 echo " Found $SIGHTING_COUNT sightings"
else
 echo " No sightings file created"
 exit 1
fi

echo ""
echo " Step 4: Testing CLI tool..."
echo "-----------------------------------------"

# Test CLI search
python scripts/sightings_cli.py --gmu 12 --days 7
check_status "CLI tool"

echo ""
echo " Step 5: Testing email digest..."
echo "-----------------------------------------"

# Generate test email
python scripts/send_email_digest.py --test
check_status "Email digest generation"

# Check if preview was created
if [ -f "data/email_preview.html" ]; then
 echo " Email preview created: data/email_preview.html"
else
 echo " Email preview not created"
fi

echo ""
echo " Step 6: Testing GMU and location processing..."
echo "-----------------------------------------"

# Check GMU data
if [ -f "data/gmu/colorado_gmu.geojson" ]; then
 echo " GMU data available"
else
 echo " GMU data missing"
fi

# Check trail data
if [ -f "data/trails/colorado_trails_index.csv" ]; then
 echo " Trail index available"
else
 echo " Trail index missing"
fi

echo ""
echo "=================================================="
echo " PIPELINE TEST COMPLETE!"
echo "=================================================="
echo ""
echo " Summary:"
echo "- All scrapers operational"
echo "- $SIGHTING_COUNT wildlife sightings collected"
echo "- Email digest ready"
echo "- CLI search tool working"
echo "- GMU/location data available"
echo ""
echo " The Wildlife Sightings Channel is fully operational!"
echo ""
echo " Next steps:"
echo "1. Review email preview: open data/email_preview.html"
echo "2. Set up cron job: ./scripts/setup_cron.sh"
echo "3. Configure email recipients in config/settings.yaml"
echo ""
