import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, JSON, Date, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class User(Base):
    """
    SQLAlchemy model for the users table.
    
    Stores basic user information and authentication details.
    Maps to Supabase auth.users table.
    """
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    user_metadata = Column(JSON, nullable=True)
    app_metadata = Column(JSON, nullable=True)
    
    # Profile fields
    name = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    weight = Column(Numeric(precision=5, scale=2), nullable=True)  # kg, up to 999.99
    height = Column(Integer, nullable=True)  # cm
    gender = Column(String(10), nullable=True)  # 'male', 'female', 'other'
    profile_photo_url = Column(String, nullable=True)
    
    # Medical conditions field - stores list of conditions with details
    medical_conditions = Column(JSON, nullable=True, default=list)
    
    # Relationships
    notifications = relationship("Notification", back_populates="user")
    ai_analysis_logs = relationship("AIAnalysisLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}', name='{self.name}')>" 