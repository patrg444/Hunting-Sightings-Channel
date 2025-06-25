#!/bin/bash

echo "====================================="
echo "Deploying 5-Day Filter Fix"
echo "====================================="
echo ""
echo "This deployment will:"
echo "1. Fix the 46 sightings issue (was using wrong API)"
echo "2. Implement 5-day data window"
echo "3. Remove generic/placeholder coordinates"
echo ""
echo "SSH to your server and run:"
echo ""
cat << 'DEPLOY_COMMANDS'
# Connect to server
ssh -i ~/.ssh/LightsailDefaultKey-us-west-2.pem ubuntu@54.203.54.74

# Navigate to project
cd /home/ubuntu/hunting-sightings

# Pull latest changes
git pull origin main

# Rebuild frontend with new API endpoint
docker-compose down
docker-compose up -d --build frontend

# Check logs
docker-compose logs -f frontend

# The frontend will now:
# - Use /api/v1/sightings endpoint (with auth)
# - Apply 5-day filter automatically
# - Filter out generic GMU coordinates
# - Show correct number of sightings
DEPLOY_COMMANDS

echo ""
echo "After deployment:"
echo "- Free users will see only sightings from last 5 days"
echo "- No more 46 static sightings"
echo "- Generic coordinates (GMU centers) filtered out"
echo ""
echo "To verify fix:"
echo "1. Open browser console (F12)"
echo "2. Look for: 'Loaded X sightings with 5-day filter'"
echo "3. Confirm X is less than 46"