from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """Base schema for users."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    academic_background: Optional[str] = None
    career_goals: Optional[str] = None
    preferred_location: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field("English", max_length=50)
    time_horizon: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating users."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating users."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    academic_background: Optional[str] = None
    career_goals: Optional[str] = None
    preferred_location: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=50)
    time_horizon: Optional[str] = Field(None, max_length=50)


class User(UserBase):
    """Schema for user responses."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SavedSearchBase(BaseModel):
    """Base schema for saved searches."""
    search_name: Optional[str] = Field(None, max_length=255)
    skills: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    location: Optional[str] = Field(None, max_length=100)
    modality: Optional[str] = Field(None, max_length=20)
    max_tuition: Optional[float] = Field(None, ge=0)
    course_level: Optional[str] = Field(None, max_length=50)


class SavedSearchCreate(SavedSearchBase):
    """Schema for creating saved searches."""
    user_id: int


class SavedSearchUpdate(BaseModel):
    """Schema for updating saved searches."""
    search_name: Optional[str] = Field(None, max_length=255)
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=100)
    modality: Optional[str] = Field(None, max_length=20)
    max_tuition: Optional[float] = Field(None, ge=0)
    course_level: Optional[str] = Field(None, max_length=50)


class SavedSearch(SavedSearchBase):
    """Schema for saved search responses."""
    id: int
    user_id: int
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteCourseRequest(BaseModel):
    """Schema for adding/removing favorite courses."""
    course_id: int


class UserProfile(User):
    """Extended user schema with relationships."""
    saved_searches: List[SavedSearch] = []
    favorite_course_count: int = 0
    
    class Config:
        from_attributes = True