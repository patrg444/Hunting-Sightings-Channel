"""Trail model for hiking trails and peaks."""

from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from geoalchemy2 import Geography
from datetime import datetime
import uuid
from app.database import Base


class Trail(Base):
    """Trail information with GMU associations."""
    
    __tablename__ = "trails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    source = Column(String(100))  # e.g., "14ers.com", "OSM"
    geometry = Column(Geography(geometry_type='LINESTRING', srid=4326))
    gmu_units = Column(ARRAY(Integer))  # GMUs the trail passes through
    elevation_gain = Column(Integer)  # in feet
    distance_miles = Column(Float)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trail {self.name}>"
