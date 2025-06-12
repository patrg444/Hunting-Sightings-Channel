#!/bin/bash
# Setup script for automated daily wildlife sightings digest

echo "=================================================="
echo "Wildlife Sightings Channel - Cron Setup"
echo "=================================================="

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_DIR/venv"
PYTHON_PATH="$VENV_PATH/bin/python"

# Create the cron command
CRON_CMD="cd $PROJECT_DIR && $PYTHON_PATH scripts/run_scrapers.py && $PYTHON_PATH scripts/send_email_digest.py"

# Daily run time (6 AM)
CRON_TIME="0 6 * * *"

# Full cron entry
CRON_ENTRY="$CRON_TIME $CRON_CMD > $PROJECT_DIR/logs/cron.log 2>&1"

echo ""
echo " Cron Schedule: Daily at 6:00 AM"
echo " Project Directory: $PROJECT_DIR"
echo " Python Path: $PYTHON_PATH"
echo ""
echo "The following cron entry will be added:"
echo "$CRON_ENTRY"
echo ""

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "run_scrapers.py"; then
 echo " WARNING: A cron entry for this project already exists!"
 echo "Current entry:"
 crontab -l | grep "run_scrapers.py"
 echo ""
 read -p "Do you want to replace it? (y/n): " -n 1 -r
 echo ""
 if [[ $REPLY =~ ^[Yy]$ ]]; then
 # Remove old entry and add new one
 (crontab -l 2>/dev/null | grep -v "run_scrapers.py"; echo "$CRON_ENTRY") | crontab -
 echo " Cron entry updated!"
 else
 echo " Setup cancelled."
 exit 1
 fi
else
 # Add new cron entry
 (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
 echo " Cron entry added!"
fi

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

echo ""
echo " Cron setup complete!"
echo ""
echo " Next steps:"
echo "1. Ensure your .env file has all required credentials"
echo "2. Test the full pipeline: ./scripts/test_full_pipeline.sh"
echo "3. Check cron logs at: $PROJECT_DIR/logs/cron.log"
echo ""
echo "To view your cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
