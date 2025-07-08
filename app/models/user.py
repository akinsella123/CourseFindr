from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for user's favorite courses
user_favorite_courses = Table(
    'user_favorite_courses',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('created_at', DateTime, server_default=func.now())
)


class User(Base):
    """User model for storing user profiles and preferences."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    
    # User preferences and background
    academic_background = Column(Text, nullable=True)
    career_goals = Column(Text, nullable=True)
    preferred_location = Column(String(100), nullable=True)
    preferred_language = Column(String(50), nullable=True, default="English")
    time_horizon = Column(String(50), nullable=True)  # this_year, next_year, flexible
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    favorite_courses = relationship("Course", secondary=user_favorite_courses, backref="favorited_by")
    saved_searches = relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class SavedSearch(Base):
    """Model for storing user's saved search queries and results."""
    
    __tablename__ = "saved_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Search parameters
    search_name = Column(String(255), nullable=True)
    skills = Column(JSON, nullable=True)  # List of skills
    interests = Column(JSON, nullable=True)  # List of interests
    location = Column(String(100), nullable=True)
    modality = Column(String(20), nullable=True)
    max_tuition = Column(Float, nullable=True)
    course_level = Column(String(50), nullable=True)
    
    # Search results (cached)
    results = Column(JSON, nullable=True)  # List of course recommendations
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_searches")
    
    def __repr__(self):
        return f"<SavedSearch(id={self.id}, user_id={self.user_id}, search_name='{self.search_name}')>"