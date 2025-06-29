#!/bin/bash
# Create Lambda deployment package with all dependencies

echo "Creating Lambda deployment package..."

# Create temp directory
TEMP_DIR="lambda_package"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Copy Lambda function
cp daily_scraper.py $TEMP_DIR/

# Copy scrapers module
cp -r ../scrapers $TEMP_DIR/

# Copy data files needed by scrapers
mkdir -p $TEMP_DIR/data
cp ../data/google_places_config.json $TEMP_DIR/data/
cp ../data/colorado_gmus.geojson $TEMP_DIR/data/

# Install dependencies
cd $TEMP_DIR
pip install -r ../requirements.txt -t . --platform manylinux2014_x86_64 --only-binary=:all:

# Remove unnecessary files to reduce package size
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
rm -rf boto* # Remove AWS SDK (provided by Lambda runtime)

# Create zip file
zip -r ../wildlife_scraper_lambda.zip . -x "*.git*"

cd ..
rm -rf $TEMP_DIR

echo "Deployment package created: wildlife_scraper_lambda.zip"
echo "Size: $(ls -lh wildlife_scraper_lambda.zip | awk '{print $5}')"