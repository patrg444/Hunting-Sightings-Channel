"""Admin endpoints for triggering scrapers."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime
import subprocess
import os
from loguru import logger

router = APIRouter(prefix="/admin", tags=["admin"])

# Simple API key authentication
API_KEY = os.environ.get("ADMIN_API_KEY", "your-secure-api-key-here")

def verify_api_key(api_key: Optional[str] = None):
    """Verify admin API key."""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

@router.post("/trigger-scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    lookback_days: int = 1,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Trigger wildlife sighting scrapers.
    This endpoint can be called by AWS Lambda for daily scraping.
    """
    
    logger.info(f"Scraping triggered with {lookback_days} day lookback")
    
    # Add scraping task to background
    background_tasks.add_task(run_scrapers, lookback_days)
    
    return {
        "status": "triggered",
        "lookback_days": lookback_days,
        "timestamp": datetime.now().isoformat()
    }

def run_scrapers(lookback_days: int):
    """Run scrapers in background."""
    try:
        # Run the scraping script
        script_path = "/app/scripts/fresh_scrape_to_supabase.py"
        
        # Check if running in Docker/production
        if not os.path.exists(script_path):
            script_path = "scripts/fresh_scrape_to_supabase.py"
        
        result = subprocess.run(
            ["python", script_path],
            env={**os.environ, "LOOKBACK_DAYS": str(lookback_days)},
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.success(f"Scraping completed successfully")
        else:
            logger.error(f"Scraping failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Error running scrapers: {e}")

@router.get("/scraping-status")
async def get_scraping_status(api_key: Optional[str] = Depends(verify_api_key)):
    """Get the status of the last scraping run."""
    
    # In a real implementation, this would check a database or cache
    return {
        "status": "ready",
        "last_run": None,
        "next_scheduled": "Daily at 2 AM UTC"
    }