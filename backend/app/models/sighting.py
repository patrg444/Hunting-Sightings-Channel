"""Sighting model for wildlife observations."""

from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from datetime import datetime
import uuid
from app.database import Base


class Sighting(Base):
    """Wildlife sighting database model."""
    
    __tablename__ = "sightings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species = Column(String(50), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    keyword_matched = Column(String(50))
    source_url = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False, index=True)
    extracted_at = Column(DateTime(timezone=True), nullable=False)
    trail_name = Column(String(255))
    sighting_date = Column(DateTime(timezone=True), index=True)
    gmu_unit = Column(Integer, index=True)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    confidence_score = Column(Float, default=1.0)
    reddit_post_title = Column(Text)
    subreddit = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Sighting {self.species} at {self.trail_name or 'Unknown'}>"
