"""
Scraper for Reddit to extract wildlife sightings from hiking-related subreddits.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Note: PRAW will be used when API credentials are available
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not available - Reddit scraper will use simulation mode")

from .base import BaseScraper
from .llm_validator import LLMValidator


class RedditScraper(BaseScraper):
    """
    Scraper for Reddit posts and comments in hiking/outdoor subreddits.
    """
    
    def __init__(self):
        super().__init__(source_name="reddit", rate_limit=1.0)
        self.reddit = None
        self.validator = LLMValidator()  # Initialize LLM validator with caching
        
        # Initialize Reddit instance if credentials are available
        if PRAW_AVAILABLE and all([
            os.getenv('REDDIT_CLIENT_ID'),
            os.getenv('REDDIT_CLIENT_SECRET'),
            os.getenv('REDDIT_USER_AGENT')
        ]):
            try:
                user_agent = os.getenv('REDDIT_USER_AGENT')
                
                # Check if it's an installed app (uses client_credentials)
                if 'installed:' in user_agent.lower():
                    # For installed apps - read-only access without password
                    self.reddit = praw.Reddit(
                        client_id=os.getenv('REDDIT_CLIENT_ID'),
                        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                        user_agent=user_agent,
                        check_for_async=False
                    )
                    logger.info("Using installed app authentication (client_credentials)")
                else:
                    # For script apps - requires username/password
                    # Fall back to read-only mode for now
                    self.reddit = praw.Reddit(
                        client_id=os.getenv('REDDIT_CLIENT_ID'),
                        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                        user_agent=user_agent,
                        check_for_async=False
                    )
                    logger.info("Using script app authentication")
                
                # Set to read-only mode
                self.reddit.read_only = True
                
                # Test the connection
                try:
                    # Simple test to verify authentication
                    _ = self.reddit.subreddit('test').id
                    logger.info("Reddit API initialized successfully in read-only mode")
                except Exception as auth_error:
                    logger.warning(f"Reddit API authentication failed: {auth_error}")
                    logger.warning("Falling back to simulation mode")
                    logger.warning("For script apps, password authentication is required but not configured")
                    logger.warning("Consider creating an 'installed app' for read-only access")
                    self.reddit = None
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
        
        # Target subreddits - hunting-focused for better wildlife sighting coverage
        subreddits = [
            'cohunting',          # Colorado-specific hunting hub
            'elkhunting',         # ~70% Colorado elk content
            'Hunting',            # Search for Colorado-specific posts
            'bowhunting',         # Bow hunters post lots of real-time sightings
            'trailcam',           # Trail-cam dumps with EXIF coords
            'Colorado',           # General state sub with wildlife pics
            'ColoradoSprings',    # Front Range wildlife sightings
            'RMNP',              # Rocky Mountain National Park
            'coloradohikers'      # Keep for incidental sightings
        ]
        
        for subreddit_name in subreddits:
            sightings = self._scrape_subreddit(subreddit_name, lookback_days)
            all_sightings.extend(sightings)
        
        logger.info(f"Found {len(all_sightings)} total sightings from Reddit")
        return all_sightings
    
    def _scrape_subreddit(self, subreddit_name: str, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Scrape a single subreddit for wildlife sightings with caching and LLM validation.
        
        Args:
            subreddit_name: Name of the subreddit
            lookback_days: Number of days to look back
            
        Returns:
            List of validated sightings from this subreddit
        """
        sightings = []
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        cache_hits = 0
        new_posts = 0
        
        if self.reddit:
            # Use actual Reddit API
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get recent posts (increased limit for 30-day lookback)
                posts_checked = 0
                for submission in subreddit.new(limit=1000):
                    posts_checked += 1
                    # Check date
                    post_date = datetime.fromtimestamp(submission.created_utc)
                    if post_date < cutoff_date:
                        break  # Stop when we reach posts older than our lookback period
                    
                    post_id = f"reddit_{submission.id}"
                    content = f"{submission.title} {submission.selftext}"
                    
                    # Check cache first
                    if not self.validator.should_process_post(post_id, content):
                        # Use cached results
                        cached_sightings = self.validator.get_cached_sightings(post_id)
                        sightings.extend(cached_sightings)
                        cache_hits += 1
                        continue
                    
                    # Process new/changed posts
                    new_posts += 1
                    
                    # Use simplified extraction - find any wildlife mentions
                    potential_mentions = self._extract_potential_wildlife_mentions(content, submission.url)
                    
                    if potential_mentions:
                        logger.debug(f"Found wildlife mentions in post: {submission.title[:50]}...")
                        # Analyze full text with LLM
                        for mention in potential_mentions:
                            analysis = self.validator.analyze_full_text_for_sighting(
                                mention['full_text'], 
                                mention['species_mentioned']
                            )
                            
                            if analysis and analysis.get('is_sighting'):
                                # Create validated sighting with location data
                                sighting = {
                                    'species': analysis['species'],
                                    'confidence': analysis['confidence'],
                                    'llm_validated': True,
                                    'reddit_post_title': submission.title,
                                    'sighting_date': post_date,
                                    'subreddit': subreddit_name,
                                    'post_id': submission.id,
                                    'source_url': mention['source_url'],
                                    'source_type': 'reddit',
                                    'raw_text': mention['full_text'][:200] + '...' if len(mention['full_text']) > 200 else mention['full_text']
                                }
                                
                                # Add location data from LLM analysis
                                location_fields = ['gmu_number', 'county', 'location_name', 'coordinates', 'elevation', 'location_description']
                                for field in location_fields:
                                    if field in analysis:
                                        sighting[field] = analysis[field]
                                
                                sightings.append(sighting)
                        
                        # Update cache with results
                        self.validator.update_cache(post_id, content, sightings)
                    else:
                        # No wildlife mentions at all
                        self.validator.update_cache(post_id, content, [])
                    
                    # Also check top comments (with caching)
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:10]:  # Top 10 comments
                        comment_id = f"reddit_comment_{comment.id}"
                        comment_content = comment.body
                        
                        # Check cache for comment
                        if not self.validator.should_process_post(comment_id, comment_content):
                            cached_comment_sightings = self.validator.get_cached_sightings(comment_id)
                            sightings.extend(cached_comment_sightings)
                            continue
                        
                        # Process new comment
                        comment_sightings = self._extract_sightings_from_text(
                            comment_content, 
                            f"https://reddit.com{comment.permalink}"
                        )
                        
                        if comment_sightings:
                            validated_comment_sightings = self.validator.validate_sightings_batch(comment_sightings)
                            
                            for sighting in validated_comment_sightings:
                                sighting['reddit_post_title'] = submission.title
                                sighting['sighting_date'] = datetime.fromtimestamp(comment.created_utc)
                                sighting['subreddit'] = subreddit_name
                                sighting['is_comment'] = True
                                sighting['comment_id'] = comment.id
                            
                            sightings.extend(validated_comment_sightings)
                            self.validator.update_cache(comment_id, comment_content, validated_comment_sightings)
                        else:
                            self.validator.update_cache(comment_id, comment_content, [])
                
                logger.info(f"r/{subreddit_name}: Checked {posts_checked} posts, processed {new_posts} new, {cache_hits} from cache, found {len(sightings)} sightings")
                        
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit_name}: {e}")
        else:
            raise Exception(f"Reddit API not available for r/{subreddit_name}. Real data only mode.")
        
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
