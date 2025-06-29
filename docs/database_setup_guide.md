# Database Setup Guide

This guide explains how to set up the database infrastructure for the Hunting Sightings Channel project to work with both the scrapers and the AWS-hosted backend.

## Overview

The project uses two database systems:
1. **SQLite** - Local database used by scrapers during development
2. **PostgreSQL with PostGIS** - Production database used by the backend API

## Database Schema Alignment

### Key Field Mappings
The scrapers and backend use slightly different field names. Here's the mapping:

| Scraper Field | Backend Field | Description |
|---------------|---------------|-------------|
| `location_name` | `trail_name` | Name of the location/trail |
| `date` | `sighting_date` | Date of the wildlife sighting |
| `description` | `raw_text` | Raw text content |
| `location_confidence_radius` | `location_confidence_radius` | Radius in miles of location accuracy |

### New Fields Added
- `location_confidence_radius` - Estimated geographical area radius (in miles) where the sighting occurred
- `content_hash` - Unique hash for deduplication

## Setup Instructions

### 1. PostgreSQL Setup

First, ensure PostgreSQL is installed with PostGIS extension:

```bash
# macOS
brew install postgresql postgis

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgis

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

### 2. Configure Environment Variables

Create or update your `.env` file:

```bash
# PostgreSQL connection for backend
DATABASE_URL=postgresql://username:password@localhost:5432/hunting_sightings

# For AWS RDS (production)
DATABASE_URL=postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/hunting_sightings
```

### 3. Create Database Schema

Run the schema creation script:

```bash
python scripts/create_backend_database_schema.py
```

This will:
- Create the database if it doesn't exist
- Enable PostGIS and UUID extensions
- Create all required tables with proper indexes
- Add the new `location_confidence_radius` field

### 4. Migrate Existing Data (Optional)

If you have existing data in SQLite:

```bash
python scripts/migrate_sqlite_to_postgres.py
```

### 5. Run Scrapers with PostgreSQL

Use the updated scraper that saves directly to PostgreSQL:

```bash
python scripts/fresh_scrape_all_postgres.py
```

## Frontend Configuration

### Development
The frontend `.env` file points to localhost by default:
```
VITE_API_URL=http://localhost:8001
```

### Production
Update `.env.production` with your AWS backend URL:
```
VITE_API_URL=https://your-api-gateway-url.amazonaws.com
```

## AWS Deployment

### RDS Setup
1. Create an RDS PostgreSQL instance with PostGIS
2. Update security groups to allow connections
3. Use the RDS endpoint in your `DATABASE_URL`

### Backend API
The FastAPI backend expects:
- PostgreSQL with PostGIS extension
- Tables created by the schema script
- Proper environment variables set

### Frontend on Vercel
1. Set environment variables in Vercel dashboard
2. Ensure `VITE_API_URL` points to your AWS API Gateway
3. Deploy frontend with production build

## Troubleshooting

### Connection Issues
- Check PostgreSQL is running
- Verify DATABASE_URL format
- Ensure PostGIS extension is installed

### Schema Mismatch
- Run `create_backend_database_schema.py` to update schema
- Check field mappings in migration script

### Rate Limiting
- LLM calls are rate-limited to ~20 seconds between requests
- Full 60-day scrape takes several hours

## Data Flow

1. **Scrapers** → Collect data with LLM validation
2. **PostgreSQL** → Store with backend-compatible schema  
3. **Backend API** → Serve data via FastAPI endpoints
4. **Frontend** → Display on Vercel-hosted React app