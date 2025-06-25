#!/bin/bash
set -e

echo "=== Deploying Hunting Sightings Channel from GitHub ==="

# Install dependencies
sudo apt-get update
sudo apt-get install -y git

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker ubuntu
    sudo systemctl enable docker
    sudo systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Clone repository
cd ~
rm -rf Hunting-Sightings-Channel
git clone https://github.com/patrg444/Hunting-Sightings-Channel.git
cd Hunting-Sightings-Channel

# Create .env file template
cat > .env << 'EOF'
# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_here
AWS_DEFAULT_REGION=us-west-2

# Google Places API
GOOGLE_PLACES_API_KEY=your_google_places_key_here

# OpenAI API
OPENAI_API_KEY=your_openai_key_here

# Database
DATABASE_URL=sqlite:///./hunting_sightings.db
SECRET_KEY=your-secret-key-here

# Supabase (optional)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
EOF

echo ""
echo "IMPORTANT: Edit the .env file to add your API keys!"
echo "Run: nano .env"
echo ""
echo "Required keys:"
echo "- AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
echo "- GOOGLE_PLACES_API_KEY" 
echo "- OPENAI_API_KEY"
echo ""
echo "Press Ctrl+C to exit and add keys, then run this script again."
echo "Press Enter to continue without API keys (limited functionality)..."
read -p ""

# Create production environment file for frontend
cat > frontend/.env.production << 'EOF'
VITE_API_URL=http://54.203.54.74:8000
EOF

# Build and start services
echo "Building services..."
sudo docker-compose -f docker-compose.production.yml build

echo "Starting services..."
sudo docker-compose -f docker-compose.production.yml up -d

# Wait for services
sleep 10

# Check status
echo "Checking service status..."
sudo docker-compose -f docker-compose.production.yml ps

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: http://54.203.54.74"
echo "Backend API: http://54.203.54.74:8000"
echo ""
echo "To view logs: sudo docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "To run Google Places scraper:"
echo "sudo docker-compose -f docker-compose.production.yml exec backend python -m scrapers.google_places_scraper"