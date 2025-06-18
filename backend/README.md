# Wildlife Sightings API - Backend

FastAPI backend for the Wildlife Sightings Channel application with Supabase authentication and PostgreSQL database.

## Features

- **Authentication**: Supabase email/password authentication with JWT tokens
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Database**: PostgreSQL with PostGIS for geospatial queries
- **Endpoints**:
  - `/api/v1/sightings` - Wildlife sightings with filtering and pagination
  - `/api/v1/users/prefs` - User preferences management
  - `/health` - Health check endpoint

## Prerequisites

- Python 3.9+
- PostgreSQL 14+ with PostGIS extension
- Supabase project (for authentication)
- Redis (optional, for caching)

## Setup

### 1. Create virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `JWT_SECRET_KEY`: Secret key for JWT tokens

### 4. Set up database

Create the database and enable PostGIS:

```sql
CREATE DATABASE wildlife_sightings;
\c wildlife_sightings
CREATE EXTENSION postgis;
```

Run the schema:

```bash
psql -U postgres -d wildlife_sightings -f database_schema.sql
```

### 5. Run the application

Development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

When running in development mode, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
All endpoints except `/health` and `/` require authentication via Bearer token in the Authorization header.

### Sightings

#### GET /api/v1/sightings
Get paginated list of wildlife sightings.

Query parameters:
- `gmu`: Filter by GMU unit (integer)
- `species`: Filter by species (string)
- `source`: Filter by source type (string)
- `start_date`: Start date filter (ISO datetime)
- `end_date`: End date filter (ISO datetime)
- `lat`: User latitude for distance calculation
- `lon`: User longitude for distance calculation
- `radius_miles`: Filter within radius (float)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

#### GET /api/v1/sightings/stats
Get statistics about wildlife sightings.

Query parameters:
- `days`: Number of days to include in stats (default: 30)

#### GET /api/v1/sightings/{sighting_id}
Get a specific sighting by ID.

### User Preferences

#### GET /api/v1/users/prefs
Get current user's preferences.

#### PUT /api/v1/users/prefs
Update user preferences.

Request body:
```json
{
  "email_notifications": true,
  "notification_time": "06:00:00",
  "gmu_filter": [12, 201],
  "species_filter": ["elk", "deer"]
}
```

#### DELETE /api/v1/users/prefs
Reset user preferences to defaults.

## Database Schema

The application uses PostgreSQL with PostGIS for geospatial queries:

- `sightings`: Wildlife sighting records with location data
- `user_preferences`: User notification preferences
- `gmus`: Game Management Unit polygons
- `trails`: Hiking trail data with GMU associations

See `database_schema.sql` for the complete schema.

## Development

### Running tests

```bash
pytest tests/
```

### Code formatting

```bash
black .
flake8 .
mypy .
```

### Database migrations

For production, use Alembic for database migrations:

```bash
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Docker Support

Build and run with Docker:

```bash
docker build -t wildlife-api .
docker run -p 8000:8000 --env-file .env wildlife-api
```

## Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

Error responses include a detail message:
```json
{
  "detail": "Error description"
}
```

## Performance Considerations

- Database indexes on frequently queried fields
- Pagination for list endpoints
- Optional Redis caching
- Connection pooling for database
- Async request handling with FastAPI

## Security

- JWT authentication via Supabase
- CORS configuration for frontend domains
- Environment variables for sensitive data
- SQL injection protection via SQLAlchemy ORM
- Rate limiting (configurable)
