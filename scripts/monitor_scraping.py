#!/usr/bin/env python3
"""
Monitor the progress of the scraping job.
"""

import sys
import os
import time
from datetime import datetime
import subprocess
import re

def get_log_stats(log_file):
    """Extract statistics from the log file."""
    
    stats = {
        'start_time': None,
        'current_time': datetime.now(),
        'reddit_subreddits': [],
        'total_posts_checked': 0,
        'total_sightings': 0,
        'errors': 0,
        'current_status': 'Unknown'
    }
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # Get start time
        if lines:
            first_line = lines[0]
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', first_line)
            if match:
                stats['start_time'] = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        
        # Process lines
        for line in lines:
            # Check for completed subreddits
            if 'Checked' in line and 'posts' in line:
                match = re.search(r'r/(\w+): Checked (\d+) posts.*found (\d+) sightings', line)
                if match:
                    subreddit = match.group(1)
                    posts = int(match.group(2))
                    sightings = int(match.group(3))
                    stats['reddit_subreddits'].append({
                        'name': subreddit,
                        'posts': posts,
                        'sightings': sightings
                    })
                    stats['total_posts_checked'] += posts
                    stats['total_sightings'] += sightings
            
            # Count errors
            if 'ERROR' in line:
                stats['errors'] += 1
            
            # Get current status (last meaningful line)
            if 'Found wildlife mentions in post:' in line:
                post_title = line.split('Found wildlife mentions in post:')[1].strip()
                stats['current_status'] = f"Processing: {post_title[:50]}"
        
        # Check if still running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'fresh_scrape' in result.stdout:
            stats['is_running'] = True
        else:
            stats['is_running'] = False
            stats['current_status'] = 'Completed or stopped'
            
    except Exception as e:
        stats['error'] = str(e)
    
    return stats

def display_progress(stats):
    """Display progress in a nice format."""
    
    print("\n" + "="*60)
    print("WILDLIFE SCRAPING PROGRESS MONITOR")
    print("="*60)
    
    if stats['start_time']:
        elapsed = stats['current_time'] - stats['start_time']
        print(f"Start Time: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Running For: {elapsed}")
    else:
        print("Start Time: Unknown")
    
    print(f"Status: {stats['current_status']}")
    print(f"Process Running: {'Yes' if stats.get('is_running', False) else 'No'}")
    
    print(f"\nProgress:")
    print(f"  Total Posts Checked: {stats['total_posts_checked']}")
    print(f"  Total Sightings Found: {stats['total_sightings']}")
    print(f"  Errors Encountered: {stats['errors']}")
    
    if stats['reddit_subreddits']:
        print(f"\nCompleted Subreddits ({len(stats['reddit_subreddits'])}):")
        for sub in stats['reddit_subreddits'][-5:]:  # Show last 5
            print(f"  - r/{sub['name']}: {sub['posts']} posts, {sub['sightings']} sightings")
    
    # Estimate completion
    total_scrapers = 4  # Reddit, Google Places, 14ers, iNaturalist
    reddit_subreddits_count = 9  # cohunting, elkhunting, Hunting, bowhunting, trailcam, Colorado, ColoradoSprings, RMNP, coloradohikers
    
    if stats['reddit_subreddits']:
        # Reddit has 9 subreddits
        reddit_progress = min(len(stats['reddit_subreddits']) / reddit_subreddits_count, 1.0)
        overall_progress = (reddit_progress / total_scrapers) * 100
        print(f"\nEstimated Progress: {overall_progress:.1f}%")
        print(f"(Reddit: {len(stats['reddit_subreddits'])}/{reddit_subreddits_count} subreddits, 3 more scrapers to go)")

def main():
    """Monitor the scraping progress."""
    
    log_file = "/Users/patrickgloria/Hunting-Sightings-Channel/fresh_scrape_full_output.log"
    
    if not os.path.exists(log_file):
        print("Error: Log file not found. Is the scraper running?")
        return
    
    # Continuous monitoring mode
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        try:
            while True:
                os.system('clear')  # Clear screen
                stats = get_log_stats(log_file)
                display_progress(stats)
                
                if not stats.get('is_running', False):
                    print("\nScraping appears to have completed!")
                    break
                    
                print("\nPress Ctrl+C to stop monitoring...")
                time.sleep(10)  # Update every 10 seconds
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        # Single run
        stats = get_log_stats(log_file)
        display_progress(stats)
        print("\nTip: Run with --watch flag for continuous monitoring")

if __name__ == "__main__":
    main()