"""GMU (Game Management Unit) model."""

from sqlalchemy import Column, String, Integer, Text
from geoalchemy2 import Geography
from app.database import Base


class GMU(Base):
    """Game Management Unit boundaries."""
    
    __tablename__ = "gmus"
    
    id = Column(Integer, primary_key=True)  # GMU number
    name = Column(String(100), nullable=False)
    geometry = Column(Geography(geometry_type='POLYGON', srid=4326), nullable=False)
    
    def __repr__(self):
        return f"<GMU {self.id}: {self.name}>"
