#!/usr/bin/env python3
"""
Test LLM-only approach: First find posts with game names, then let LLM decide.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.reddit_scraper import RedditScraper
from scrapers.llm_validator import LLMValidator
from loguru import logger
from rich.console import Console
from rich import print as rprint
import re

console = Console()

def test_llm_only_approach():
 """Test the two-step approach: parse game names, then LLM validation."""
 console.print("\n[bold cyan]Testing LLM-Only Wildlife Detection[/bold cyan]")
 console.print("=" * 70)

 # Initialize components
 scraper = RedditScraper()
 validator = LLMValidator()

 # Check LLM status
 if validator.llm_available:
 console.print("[green] LLM (OpenAI) is available and ready[/green]")
 else:
 console.print("[red] LLM not available - check OpenAI API key[/red]")
 return

 if not scraper.reddit:
 console.print("[red] Reddit API not available[/red]")
 return

 # Game species to look for
 game_keywords = {
 'elk': ['elk', 'bull', 'cow', 'wapiti'],
 'deer': ['deer', 'buck', 'doe', 'muley', 'mule deer', 'whitetail'],
 'bear': ['bear', 'black bear', 'griz', 'grizzly'],
 'pronghorn': ['pronghorn', 'antelope', 'speed goat'],
 'bighorn_sheep': ['bighorn', 'sheep', 'ram'],
 'mountain_goat': ['mountain goat', 'goat', 'billy', 'nanny'],
 'moose': ['moose', 'bull moose', 'cow moose']
 }

 # Test subreddit
 subreddit_name = 'cohunting'
 console.print(f"\n[yellow]Analyzing r/{subreddit_name} with LLM validation[/yellow]")

 try:
 subreddit = scraper.reddit.subreddit(subreddit_name)
 posts_with_game = 0
 validated_sightings = 0

 # Get recent posts
 for i, submission in enumerate(subreddit.new(limit=20)):
 full_text = f"{submission.title} {submission.selftext}"

 # Step 1: Check if ANY game species mentioned
 species_found = []
 for species, keywords in game_keywords.items():
 for keyword in keywords:
 pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
 if re.search(pattern, full_text.lower()):
 species_found.append(species)
 break

 if species_found:
 posts_with_game += 1
 console.print(f"\n[green]Post {i+1}: Contains game species: {', '.join(set(species_found))}[/green]")
 console.print(f"Title: {submission.title}")

 # Step 2: Let LLM analyze the full text
 console.print("[yellow]Sending to LLM for analysis...[/yellow]")

 analysis = validator.analyze_full_text_for_sighting(
 full_text[:1000], # Limit to 1000 chars for cost
 list(set(species_found))
 )

 if analysis and analysis.get('is_sighting'):
 validated_sightings += 1
 console.print(f"[bold green] LLM: CONFIRMED SIGHTING[/bold green]")
 console.print(f" Species: {analysis['species']}")
 console.print(f" Confidence: {analysis['confidence']*100:.0f}%")
 else:
 console.print("[red] LLM: Not a real sighting[/red]")

 # Show a bit of the text
 preview = submission.selftext[:200] + "..." if len(submission.selftext) > 200 else submission.selftext
 if preview:
 console.print(f"Text preview: {preview}")

 # Summary
 console.print(f"\n[bold cyan]Summary:[/bold cyan]")
 console.print(f"Posts analyzed: 20")
 console.print(f"Posts with game species mentioned: {posts_with_game}")
 console.print(f"Validated wildlife sightings: {validated_sightings}")
 console.print(f"Success rate: {validated_sightings/posts_with_game*100:.1f}%" if posts_with_game > 0 else "N/A")

 except Exception as e:
 console.print(f"[red]Error: {e}[/red]")
 import traceback
 traceback.print_exc()

if __name__ == "__main__":
 test_llm_only_approach()
