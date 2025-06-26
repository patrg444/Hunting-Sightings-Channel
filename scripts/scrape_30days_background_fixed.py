#!/usr/bin/env python3
"""
Fixed background 30-day scraper with proper geometry formatting.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from supabase import create_client
from loguru import logger
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))

from processors.gmu_processor import GMUProcessor

# Initialize GMU processor
gmu_processor = GMUProcessor()
gmu_processor.load_gmu_data()

# Load GMU centers
with open('data/gmu_centers.json', 'r') as f:
    GMU_CENTERS = json.load(f)

# Configure environment
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
os.environ['REDDIT_CLIENT_ID'] = os.getenv('REDDIT_CLIENT_ID', '')
os.environ['REDDIT_CLIENT_SECRET'] = os.getenv('REDDIT_CLIENT_SECRET', '')
os.environ['REDDIT_USER_AGENT'] = os.getenv('REDDIT_USER_AGENT', 'Wildlife Sightings Bot 1.0')
os.environ['GOOGLE_PLACES_API_KEY'] = os.getenv('GOOGLE_PLACES_API_KEY', '')

# Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rvrdbtrxwndeerqmziuo.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')

# Configure logging
logger.add("logs/background_scrape_fixed_{time}.log", rotation="1 day")

# Progress file
PROGRESS_FILE = Path("data/scraper_progress_fixed.json")

def load_progress():
    """Load progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'start_time': datetime.now().isoformat(),
        'reddit': {'status': 'pending', 'subreddits_completed': [], 'posts_processed': 0, 'sightings_found': 0, 'sightings_stored': 0},
        'inaturalist': {'status': 'pending', 'observations_processed': 0, 'sightings_found': 0, 'sightings_stored': 0},
        'google_places': {'status': 'pending', 'places_processed': 0, 'sightings_found': 0, 'sightings_stored': 0},
        'last_update': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save progress to file."""
    progress['last_update'] = datetime.now().isoformat()
    PROGRESS_FILE.parent.mkdir(exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def store_sighting(supabase, sighting_data, source_type):
    """Store a sighting with proper geometry formatting."""
    try:
        logger.debug(f"Storing {source_type} sighting: {json.dumps(sighting_data, default=str)[:200]}...")
        # Parse date
        sighting_date = sighting_data.get('date') or sighting_data.get('sighting_date') or datetime.now().date()
        if isinstance(sighting_date, str):
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    sighting_date = datetime.strptime(sighting_date.split('.')[0].split('+')[0], fmt).date()
                    break
                except:
                    continue
        
        if hasattr(sighting_date, 'isoformat'):
            sighting_date = sighting_date.isoformat()
        
        # Extract coordinates
        lat = sighting_data.get('latitude') or (sighting_data.get('location', {}).get('lat') if isinstance(sighting_data.get('location'), dict) else None)
        lon = sighting_data.get('longitude') or (sighting_data.get('location', {}).get('lon') if isinstance(sighting_data.get('location'), dict) else None)
        
        # Check for coordinates from LLM validator
        if not lat and not lon and sighting_data.get('coordinates'):
            coords = sighting_data['coordinates']
            if isinstance(coords, list) and len(coords) == 2:
                lat, lon = coords[0], coords[1]
                logger.debug(f"Extracted LLM coordinates: {lat}, {lon}")
        
        # Get GMU info from LLM or calculate from coordinates
        gmu_unit = sighting_data.get('gmu_unit') or sighting_data.get('gmu_number')
        
        # If we have coordinates but no GMU, find which GMU contains the point
        if lat and lon and not gmu_unit:
            try:
                gmu_unit = gmu_processor.find_gmu_for_point(lat, lon)
                if gmu_unit:
                    logger.debug(f"Found GMU {gmu_unit} for coordinates {lat}, {lon}")
            except Exception as e:
                logger.debug(f"Could not determine GMU: {e}")
        
        # If we have GMU but no coordinates, use GMU center
        if gmu_unit and not (lat and lon):
            gmu_str = str(gmu_unit)
            if gmu_str in GMU_CENTERS:
                center = GMU_CENTERS[gmu_str]['center']
                lat, lon = center[0], center[1]
                logger.debug(f"Using GMU {gmu_unit} center: {lat}, {lon}")
        
        # Extract location name
        location_name = None
        if isinstance(sighting_data.get('location'), dict):
            location_name = sighting_data['location'].get('place_guess') or sighting_data['location'].get('name')
        elif isinstance(sighting_data.get('location'), str):
            location_name = sighting_data['location']
        
        # Build record with proper fields
        data = {
            'species': sighting_data.get('species', 'Unknown'),
            'location_name': location_name or sighting_data.get('location_name', 'Unknown'),
            'sighting_date': sighting_date,
            'description': sighting_data.get('description', ''),
            'raw_text': sighting_data.get('raw_text', sighting_data.get('description', '')),
            'source_type': source_type,
            'source_url': sighting_data.get('source_url', sighting_data.get('url', sighting_data.get('inaturalist_url', ''))),
            'confidence_score': sighting_data.get('confidence_score', sighting_data.get('confidence', 0.5)),
        }
        
        # Add GMU unit as integer if we have it
        if gmu_unit:
            try:
                data['gmu_unit'] = int(gmu_unit)
            except (ValueError, TypeError):
                logger.debug(f"Could not convert GMU {gmu_unit} to integer")
        
        # Add location as PostGIS format if we have coordinates
        if lat and lon:
            data['location'] = f"POINT({float(lon)} {float(lat)})"
        
        # Check if exists
        if data['source_url']:
            existing = supabase.table('sightings').select('id').eq('source_url', data['source_url']).execute()
            if not existing.data:
                result = supabase.table('sightings').insert(data).execute()
                logger.info(f"✓ Stored: {data['species']} at {location_name or 'Unknown'} on {sighting_date}")
                return True
            else:
                logger.debug(f"Skipping duplicate: {data['source_url']}")
        else:
            logger.warning(f"No URL for sighting: {data['species']} from {source_type}")
            
    except Exception as e:
        logger.error(f"Error storing {source_type} sighting: {e}")
        logger.debug(f"Sighting data: {sighting_data}")
    return False

class ProgressTrackingRedditScraper:
    """Reddit scraper that saves sightings immediately and tracks progress."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        from scrapers.reddit_scraper import RedditScraper
        self.scraper = RedditScraper()
        self.progress = load_progress()
        
    def scrape_with_progress(self, lookback_days=30):
        """Scrape Reddit with progress tracking and immediate saving."""
        subreddits = [
            'cohunting', 'elkhunting', 'Hunting', 'bowhunting', 
            'trailcam', 'Colorado', 'ColoradoSprings', 'RMNP', 'coloradohikers'
        ]
        
        # Start or resume Reddit scraping
        self.progress['reddit']['status'] = 'in_progress'
        save_progress(self.progress)
        
        total_sightings = 0
        total_stored = 0
        
        for subreddit in subreddits:
            if subreddit in self.progress['reddit']['subreddits_completed']:
                logger.info(f"Skipping already completed subreddit: r/{subreddit}")
                continue
                
            logger.info(f"\nProcessing r/{subreddit}...")
            
            # Scrape subreddit
            sightings = self.scraper._scrape_subreddit(subreddit, lookback_days=lookback_days)
            
            # Save each sighting immediately
            stored_count = 0
            for sighting in sightings:
                if store_sighting(self.supabase, sighting, 'reddit'):
                    stored_count += 1
                    total_stored += 1
            
            # Update progress
            self.progress['reddit']['posts_processed'] += 100  # Approximate
            self.progress['reddit']['sightings_found'] += len(sightings)
            self.progress['reddit']['sightings_stored'] += stored_count
            self.progress['reddit']['subreddits_completed'].append(subreddit)
            save_progress(self.progress)
            
            logger.info(f"r/{subreddit}: Found {len(sightings)} sightings, stored {stored_count}")
            total_sightings += len(sightings)
        
        self.progress['reddit']['status'] = 'completed'
        save_progress(self.progress)
        
        return total_sightings, total_stored

def main():
    """Run the background scraper with fixed geometry."""
    try:
        # Initialize Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Connected to Supabase")
        
        # Initialize progress
        progress = load_progress()
        
        # 1. Reddit
        if progress['reddit']['status'] != 'completed':
            logger.info("=== Starting Reddit Scraping ===")
            reddit_scraper = ProgressTrackingRedditScraper(supabase)
            reddit_total, reddit_stored = reddit_scraper.scrape_with_progress(lookback_days=30)
            logger.info(f"Reddit complete: {reddit_total} found, {reddit_stored} stored")
        
        # 2. iNaturalist
        if progress['inaturalist']['status'] != 'completed':
            logger.info("\n=== Starting iNaturalist Scraping ===")
            progress['inaturalist']['status'] = 'in_progress'
            save_progress(progress)
            
            from scrapers.inaturalist_scraper import INaturalistScraper
            inaturalist_scraper = INaturalistScraper()
            observations = inaturalist_scraper.scrape(lookback_days=30)
            
            stored_count = 0
            for obs in observations:
                if store_sighting(supabase, obs, 'inaturalist'):
                    stored_count += 1
            
            progress['inaturalist']['status'] = 'completed'
            progress['inaturalist']['observations_processed'] = len(observations)
            progress['inaturalist']['sightings_found'] = len(observations)
            progress['inaturalist']['sightings_stored'] = stored_count
            save_progress(progress)
            
            logger.info(f"iNaturalist complete: {len(observations)} found, {stored_count} stored")
        
        # 3. Google Places
        if progress['google_places']['status'] != 'completed':
            logger.info("\n=== Starting Google Places Scraping ===")
            progress['google_places']['status'] = 'in_progress'
            save_progress(progress)
            
            from scrapers.google_places_scraper import GooglePlacesScraper
            places_scraper = GooglePlacesScraper()
            wildlife_areas = places_scraper.scrape(lookback_days=30)
            
            stored_count = 0
            for area in wildlife_areas:
                if store_sighting(supabase, area, 'google_places'):
                    stored_count += 1
            
            progress['google_places']['status'] = 'completed'
            progress['google_places']['places_processed'] = len(wildlife_areas)
            progress['google_places']['sightings_found'] = len(wildlife_areas)
            progress['google_places']['sightings_stored'] = stored_count
            save_progress(progress)
            
            logger.info(f"Google Places complete: {len(wildlife_areas)} found, {stored_count} stored")
        
        logger.info("\n=== Scraping Complete ===")
        logger.info(f"Reddit: {progress['reddit']['sightings_stored']} stored")
        logger.info(f"iNaturalist: {progress['inaturalist']['sightings_stored']} stored")
        logger.info(f"Google Places: {progress['google_places']['sightings_stored']} stored")
        
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        raise

if __name__ == "__main__":
    main()