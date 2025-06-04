"""
Scraper for Reddit to extract wildlife sightings from hiking-related subreddits.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

# Note: PRAW will be used when API credentials are available
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not available - Reddit scraper will use simulation mode")

from .base import BaseScraper


class RedditScraper(BaseScraper):
    """
    Scraper for Reddit posts and comments in hiking/outdoor subreddits.
    """
    
    def __init__(self):
        super().__init__(source_name="reddit", rate_limit=1.0)
        self.reddit = None
        
        # Initialize Reddit instance if credentials are available
        if PRAW_AVAILABLE and all([
            os.getenv('REDDIT_CLIENT_ID'),
            os.getenv('REDDIT_CLIENT_SECRET'),
            os.getenv('REDDIT_USER_AGENT')
        ]):
            try:
                self.reddit = praw.Reddit(
                    client_id=os.getenv('REDDIT_CLIENT_ID'),
                    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                    user_agent=os.getenv('REDDIT_USER_AGENT')
                )
                logger.info("Reddit API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit API: {e}")
                self.reddit = None
        
    def scrape(self, lookback_days: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape recent posts from Colorado hiking subreddits.
        
        Args:
            lookback_days: Number of days to look back for posts
            
        Returns:
            List of wildlife sightings
        """
        all_sightings = []
        
        # Target subreddits from config
        subreddits = ['14ers', 'coloradohikers', 'ColoradoHunting']
        
        for subreddit_name in subreddits:
            sightings = self._scrape_subreddit(subreddit_name, lookback_days)
            all_sightings.extend(sightings)
        
        logger.info(f"Found {len(all_sightings)} total sightings from Reddit")
        return all_sightings
    
    def _scrape_subreddit(self, subreddit_name: str, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Scrape a single subreddit for wildlife sightings.
        
        Args:
            subreddit_name: Name of the subreddit
            lookback_days: Number of days to look back
            
        Returns:
            List of sightings from this subreddit
        """
        sightings = []
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        if self.reddit:
            # Use actual Reddit API
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get recent posts
                for submission in subreddit.new(limit=100):
                    # Check date
                    post_date = datetime.fromtimestamp(submission.created_utc)
                    if post_date < cutoff_date:
                        continue
                    
                    # Extract from title and selftext
                    text = f"{submission.title} {submission.selftext}"
                    post_sightings = self._extract_sightings_from_text(text, submission.url)
                    
                    # Add metadata
                    for sighting in post_sightings:
                        sighting['reddit_post_title'] = submission.title
                        sighting['sighting_date'] = post_date
                        sighting['subreddit'] = subreddit_name
                    
                    sightings.extend(post_sightings)
                    
                    # Also check top comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:10]:  # Top 10 comments
                        comment_sightings = self._extract_sightings_from_text(
                            comment.body, 
                            f"https://reddit.com{comment.permalink}"
                        )
                        
                        for sighting in comment_sightings:
                            sighting['reddit_post_title'] = submission.title
                            sighting['sighting_date'] = datetime.fromtimestamp(comment.created_utc)
                            sighting['subreddit'] = subreddit_name
                            sighting['is_comment'] = True
                        
                        sightings.extend(comment_sightings)
                        
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit_name}: {e}")
        else:
            # Simulation mode with sample data
            sightings.extend(self._get_simulated_posts(subreddit_name))
        
        return sightings
    
    def _get_simulated_posts(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Get simulated Reddit posts for testing without API access.
        
        Args:
            subreddit_name: Name of the subreddit
            
        Returns:
            List of simulated sightings
        """
        simulated_sightings = []
        
        # Sample posts by subreddit
        sample_posts = {
            '14ers': [
                {
                    'title': 'Mt. Elbert Trip Report - Beautiful sunrise and wildlife!',
                    'text': """Just got back from Mt. Elbert via the East Ridge. Started at 3:30am to catch the sunrise. 
                    About an hour in, we spotted a large herd of elk crossing the trail below treeline. Must have been 
                    20-30 of them! Also saw a black bear in the distance near Twin Lakes on the drive out. 
                    Perfect weather and no crowds on a Tuesday.""",
                    'url': 'https://reddit.com/r/14ers/comments/sample1'
                },
                {
                    'title': 'Grays and Torreys Double - Mountain Goat Encounter',
                    'text': """Did the Grays/Torreys combo yesterday. The mountain goats were out in full force! 
                    Saw a group of 6 including 2 kids on the traverse between the peaks. They were super chill and 
                    let us pass within about 50 feet. Remember to give wildlife space! Also heard there were 
                    bighorn sheep spotted near the Stevens Gulch trailhead last weekend.""",
                    'url': 'https://reddit.com/r/14ers/comments/sample2'
                }
            ],
            'coloradohikers': [
                {
                    'title': 'RMNP - Chasm Lake hike wildlife sighting',
                    'text': """Hiked to Chasm Lake yesterday (6/2). The trail conditions were perfect - mostly dry with 
                    some snow near the lake. Best part was seeing a small group of bighorn sheep on the rocky slopes 
                    above Peacock Pool. They were pretty far off but got some decent photos with my zoom lens. 
                    Also tons of marmots near the lake itself. No sign of the bear that was reported last week.""",
                    'url': 'https://reddit.com/r/coloradohikers/comments/sample3'
                },
                {
                    'title': 'Lost Creek Wilderness - Overnight Trip Report',
                    'text': """Just finished a 2-night trip in Lost Creek. The wildflowers are starting! Day 1 we saw 
                    a huge bull elk near Brookside-McCurdy trail junction. He was just grazing and didn't seem bothered 
                    by us. Day 2 had fresh bear tracks on the trail but never saw the bear itself. Hung our food properly 
                    just in case. Also spooked some deer near camp on the last morning.""",
                    'url': 'https://reddit.com/r/coloradohikers/comments/sample4'
                }
            ],
            'ColoradoHunting': [
                {
                    'title': 'Scouting GMU 12 - Elk activity',
                    'text': """Was up scouting GMU 12 this past weekend. Lots of fresh elk sign on the north-facing 
                    slopes between 9,500-11,000 ft. Spotted two different herds - one group of cows and calves 
                    (maybe 15-20) and a bachelor group with 4 bulls. The bigger bulls are already starting to shed 
                    their velvet. Also jumped a black bear on one of the old logging roads.""",
                    'url': 'https://reddit.com/r/ColoradoHunting/comments/sample5'
                }
            ]
        }
        
        # Process simulated posts
        posts = sample_posts.get(subreddit_name, [])
        for post in posts:
            text = f"{post['title']} {post['text']}"
            post_sightings = self._extract_sightings_from_text(text, post['url'])
            
            # Add metadata
            for sighting in post_sightings:
                sighting['reddit_post_title'] = post['title']
                sighting['sighting_date'] = datetime.now() - timedelta(days=1)
                sighting['subreddit'] = subreddit_name
                
                # Try to infer trail name from title/text
                if 'Mt. Elbert' in text:
                    sighting['trail_name'] = 'Mt. Elbert'
                elif 'Grays' in text or 'Torreys' in text:
                    sighting['trail_name'] = 'Grays Peak'
                elif 'Chasm Lake' in text:
                    sighting['trail_name'] = 'Longs Peak'
                
            simulated_sightings.extend(post_sightings)
        
        return simulated_sightings
    
    def get_trail_locations(self) -> List[Dict[str, Any]]:
        """
        Reddit doesn't provide structured trail location data.
        
        Returns:
            Empty list
        """
        return []
