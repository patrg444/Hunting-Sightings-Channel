#!/usr/bin/env python3
"""
Email digest sender for wildlife sightings.
Sends daily email summaries of wildlife sightings to subscribers.
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jinja2 import Environment, FileSystemLoader
from loguru import logger
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailDigestSender:
 """Sends email digests of wildlife sightings."""

 def __init__(self):
 """Initialize email sender with configuration."""
 # Load config
 with open('config/settings.yaml', 'r') as f:
 self.config = yaml.safe_load(f)

 # Email configuration from environment
 self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
 self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
 self.smtp_username = os.getenv('SMTP_USERNAME')
 self.smtp_password = os.getenv('SMTP_PASSWORD')
 self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)

 # Template setup
 self.template_dir = Path('templates')
 self.env = Environment(loader=FileSystemLoader(self.template_dir))
 self.template = self.env.get_template('email_digest.html')

 def load_recent_sightings(self, hours: int = 24) -> List[Dict[str, Any]]:
 """
 Load sightings from the last N hours.

 Args:
 hours: Number of hours to look back

 Returns:
 List of sighting dictionaries
 """
 # Load from the latest sightings file
 sightings_file = Path('data/sightings/latest_sightings.json')

 if not sightings_file.exists():
 logger.warning("No sightings file found")
 return []

 with open(sightings_file, 'r') as f:
 all_sightings = json.load(f)

 # Filter by date
 cutoff_date = datetime.now() - timedelta(hours=hours)
 recent_sightings = []

 for sighting in all_sightings:
 try:
 # Parse sighting date
 sighting_date = datetime.fromisoformat(
 sighting.get('sighting_date', '').replace('Z', '+00:00')
 )

 if sighting_date >= cutoff_date:
 recent_sightings.append(sighting)
 except Exception as e:
 logger.debug(f"Error parsing date for sighting: {e}")
 continue

 return recent_sightings

 def prepare_digest_data(self, sightings: List[Dict[str, Any]]) -> Dict[str, Any]:
 """
 Prepare data for the email template.

 Args:
 sightings: List of sighting dictionaries

 Returns:
 Dictionary of template variables
 """
 # Count species
 species_counter = Counter(s.get('species', 'unknown') for s in sightings)

 # Count GMUs
 gmus = set()
 for s in sightings:
 if s.get('gmu_number'):
 gmus.add(s['gmu_number'])

 # Count sources
 sources = set(s.get('source', 'unknown') for s in sightings)

 # Prepare template data
 return {
 'date': datetime.now().strftime('%B %d, %Y'),
 'sightings': sightings,
 'species_count': len(species_counter),
 'gmu_count': len(gmus),
 'source_count': len(sources),
 'species_summary': dict(species_counter)
 }

 def render_html(self, sightings: List[Dict[str, Any]]) -> str:
 """
 Render HTML email content.

 Args:
 sightings: List of sighting dictionaries

 Returns:
 Rendered HTML string
 """
 data = self.prepare_digest_data(sightings)
 return self.template.render(**data)

 def send_email(self, to_emails: List[str], subject: str, html_content: str) -> bool:
 """
 Send email to recipients.

 Args:
 to_emails: List of recipient email addresses
 subject: Email subject
 html_content: HTML email content

 Returns:
 True if sent successfully
 """
 if not self.smtp_username or not self.smtp_password:
 logger.error("SMTP credentials not configured in environment")
 return False

 try:
 # Create message
 msg = MIMEMultipart('alternative')
 msg['Subject'] = subject
 msg['From'] = self.from_email
 msg['To'] = ', '.join(to_emails)

 # Attach HTML content
 html_part = MIMEText(html_content, 'html')
 msg.attach(html_part)

 # Send email
 with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
 server.starttls()
 server.login(self.smtp_username, self.smtp_password)
 server.send_message(msg)

 logger.info(f"Email sent successfully to {len(to_emails)} recipients")
 return True

 except Exception as e:
 logger.error(f"Failed to send email: {e}")
 return False

 def send_digest(self, recipient_emails: Optional[List[str]] = None) -> bool:
 """
 Send the wildlife sightings digest.

 Args:
 recipient_emails: List of email addresses (uses config if not provided)

 Returns:
 True if sent successfully
 """
 # Get recipients
 if not recipient_emails:
 recipient_emails = self.config.get('email', {}).get('recipients', [])

 if not recipient_emails:
 logger.warning("No email recipients configured")
 return False

 # Load recent sightings
 sightings = self.load_recent_sightings(hours=24)
 logger.info(f"Found {len(sightings)} sightings in the last 24 hours")

 # Render email
 html_content = self.render_html(sightings)

 # Save a copy for preview
 preview_file = Path('data/email_preview.html')
 preview_file.parent.mkdir(exist_ok=True)
 with open(preview_file, 'w') as f:
 f.write(html_content)
 logger.info(f"Email preview saved to: {preview_file}")

 # Send email
 subject = f"Wildlife Sightings Digest - {datetime.now().strftime('%B %d, %Y')}"

 # If SMTP is not configured, just save the preview
 if not self.smtp_username:
 logger.warning("SMTP not configured - email preview saved only")
 return True

 return self.send_email(recipient_emails, subject, html_content)

def main():
 """Run the email digest sender."""
 logger.info("Starting email digest sender...")

 sender = EmailDigestSender()

 # Check for test mode
 if len(sys.argv) > 1 and sys.argv[1] == '--test':
 logger.info("Running in test mode - generating preview only")
 test_sightings = [
 {
 'species': 'elk',
 'source': 'reddit',
 'trail_name': 'Mount Elbert',
 'gmu_number': 49,
 'elevation': 12500,
 'sighting_date': datetime.now().isoformat(),
 'raw_text': 'Saw a herd of 20+ elk on the northeast ridge of Mount Elbert this morning. Beautiful sight!'
 },
 {
 'species': 'mountain_goat',
 'source': '14ers.com',
 'location_name': 'Capitol Peak',
 'gmu_number': 47,
 'elevation': 13500,
 'sighting_date': (datetime.now() - timedelta(hours=3)).isoformat(),
 'raw_text': 'Three mountain goats spotted near the knife edge. They seemed very comfortable on the exposed rock.'
 },
 {
 'species': 'black_bear',
 'source': 'summitpost',
 'trail_name': 'Longs Peak',
 'gmu_number': 20,
 'elevation': 11000,
 'sighting_date': (datetime.now() - timedelta(hours=8)).isoformat(),
 'raw_text': 'Black bear sighting near the Chasm Lake junction. Keep your distance and store food properly!'
 }
 ]

 html_content = sender.render_html(test_sightings)
 preview_file = Path('data/email_preview.html')
 preview_file.parent.mkdir(exist_ok=True)
 with open(preview_file, 'w') as f:
 f.write(html_content)

 print(f"\n Test email preview generated: {preview_file}")
 print(" Open this file in a browser to see the email layout")

 else:
 # Send actual digest
 success = sender.send_digest()

 if success:
 print("\n Email digest sent successfully!")
 else:
 print("\n Failed to send email digest")
 print(" Check logs for details")

if __name__ == "__main__":
 main()
