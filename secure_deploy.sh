#!/bin/bash
set -e

echo "=== Secure AWS Deployment ==="
echo "Deploying to EC2 instance at 54.203.54.74"

SSH_KEY="$HOME/.ssh/hunting-deploy.pem"
EC2_USER="ubuntu"
EC2_IP="54.203.54.74"

# First commit and push code changes without secrets
echo "Committing code changes (without secrets)..."
git add -A
git diff --cached --name-only | grep -E "(remote_deploy|secure_deploy)" | xargs git reset HEAD -- 2>/dev/null || true
git commit -m "Deploy: Update frontend and backend with latest features" || echo "No changes to commit"
git push origin main || echo "Failed to push - continuing anyway"

# Deploy on server
echo "Connecting to server and deploying..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_IP" << 'DEPLOY'
set -e

cd ~/Hunting-Sightings-Channel || {
    echo "Project not found. Cloning..."
    cd ~
    git clone https://github.com/patrg444/Hunting-Sightings-Channel.git
    cd Hunting-Sightings-Channel
}

# Pull latest changes
echo "Pulling latest changes..."
git fetch origin
git reset --hard origin/main

# Backend deployment
echo "Deploying backend..."
cd backend

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p ../logs

# Stop existing services
echo "Stopping existing services..."
pkill -f "uvicorn" || true
pkill -f "api_coordinate_fix" || true
pkill -f "api_remove_duplicates" || true
sleep 3

# Start backend services
echo "Starting backend services..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
nohup python api_coordinate_fix.py > ../logs/api_coordinate_fix.log 2>&1 &
nohup python api_remove_duplicates.py > ../logs/api_remove_duplicates.log 2>&1 &

cd ..

# Frontend deployment
echo "Deploying frontend..."
cd frontend

# Install Node.js if needed
if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install dependencies and build
npm install
npm run build

# Setup nginx if needed
if [ ! -f /etc/nginx/sites-available/hunting-sightings ]; then
    echo "Configuring nginx..."
    sudo tee /etc/nginx/sites-available/hunting-sightings > /dev/null << 'NGINX'
server {
    listen 80;
    server_name 54.203.54.74;
    
    root /home/ubuntu/Hunting-Sightings-Channel/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX
    
    sudo ln -sf /etc/nginx/sites-available/hunting-sightings /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl restart nginx
fi

cd ..

# Check services
echo ""
echo "=== Checking services ==="
ps aux | grep -E "uvicorn|api_coordinate" | grep -v grep || echo "Services not running!"

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: http://54.203.54.74"
echo "Backend API: http://54.203.54.74/api/v1/health"
DEPLOY

echo ""
echo "Deployment script completed!"
echo ""
echo "IMPORTANT: You need to manually update the .env file on the server with your credentials."
echo "Run: ssh -i $SSH_KEY $EC2_USER@$EC2_IP"
echo "Then: nano ~/Hunting-Sightings-Channel/.env"