"""User preferences model."""

from sqlalchemy import Column, String, Boolean, Time, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, time
import uuid
from app.database import Base


class UserPreferences(Base):
    """User preferences for wildlife sighting notifications."""
    
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)  # From Supabase auth.users
    email_notifications = Column(Boolean, default=True)
    notification_time = Column(Time, default=time(6, 0))  # 6 AM default
    gmu_filter = Column(ARRAY(Integer), default=list)  # Empty array = all GMUs
    species_filter = Column(ARRAY(String), default=list)  # Empty array = all species
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreferences user_id={self.user_id}>"
