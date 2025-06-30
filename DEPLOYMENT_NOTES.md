# Deployment Notes for huntsightings.com

## Current Status
- AWS deployment at http://54.203.54.74/ is working correctly with 294 markers displayed
- Production site at https://www.huntsightings.com/ needs updating

## Important Issue: HTTPS/HTTP Mixed Content
The production site (huntsightings.com) uses HTTPS, but our backend API at 54.203.54.74:8000 only supports HTTP. This creates a "mixed content" security issue where browsers block HTTP requests from HTTPS sites.

## Solutions:

### Option 1: Configure HTTPS on Backend (Recommended)
Add SSL/TLS certificate to the backend server at 54.203.54.74:
```bash
# Using Let's Encrypt with nginx reverse proxy
sudo apt-get install nginx certbot python3-certbot-nginx
# Configure nginx as reverse proxy
# Run certbot to get SSL certificate
```

### Option 2: Use Vercel Rewrites (Temporary)
Add to `vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://54.203.54.74:8000/api/:path*"
    }
  ]
}
```
Note: This may not work due to Vercel's security policies.

### Option 3: Deploy Backend to HTTPS Service
Deploy the backend to a service that provides HTTPS by default:
- Vercel Functions
- AWS API Gateway + Lambda
- Heroku
- Railway

## Current Configuration
- Frontend: Latest code pushed to GitHub
- Backend: Running on AWS at http://54.203.54.74:8000
- Database: Supabase PostgreSQL with 327 geocoded sightings

## Vercel Deployment
The site should auto-deploy when changes are pushed to the main branch. If not:
1. Log into Vercel dashboard
2. Check deployment logs
3. Ensure environment variables are set in Vercel:
   - VITE_SUPABASE_URL
   - VITE_SUPABASE_ANON_KEY
   - VITE_API_URL (needs HTTPS endpoint)

## Verification
After deployment, verify:
1. Map shows 200+ markers
2. Filters work correctly
3. 100-mile accuracy filter is default
4. API calls succeed (check browser console)