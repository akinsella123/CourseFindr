from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Base schema for skills."""
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class SkillCreate(SkillBase):
    """Schema for creating skills."""
    pass


class Skill(SkillBase):
    """Schema for skill responses."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CareerOutcomeBase(BaseModel):
    """Base schema for career outcomes."""
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    average_salary: Optional[float] = None
    salary_currency: Optional[str] = Field("USD", max_length=3)
    employment_rate: Optional[float] = Field(None, ge=0, le=100)


class CareerOutcomeCreate(CareerOutcomeBase):
    """Schema for creating career outcomes."""
    pass


class CareerOutcome(CareerOutcomeBase):
    """Schema for career outcome responses."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    """Base schema for courses."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    institution: str = Field(..., max_length=255)
    location_city: Optional[str] = Field(None, max_length=100)
    location_country: Optional[str] = Field(None, max_length=100)
    language_of_instruction: str = Field("English", max_length=50)
    modality: str = Field("in-person", max_length=20)
    duration_months: Optional[int] = Field(None, gt=0)
    tuition_fee: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field("USD", max_length=3)
    entry_requirements: Optional[str] = None
    application_deadline: Optional[datetime] = None
    university_rank: Optional[int] = Field(None, gt=0)
    course_level: Optional[str] = Field(None, max_length=50)
    course_code: Optional[str] = Field(None, max_length=50)


class CourseCreate(CourseBase):
    """Schema for creating courses."""
    skill_ids: Optional[List[int]] = []
    career_outcome_ids: Optional[List[int]] = []


class CourseUpdate(BaseModel):
    """Schema for updating courses."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    institution: Optional[str] = Field(None, max_length=255)
    location_city: Optional[str] = Field(None, max_length=100)
    location_country: Optional[str] = Field(None, max_length=100)
    language_of_instruction: Optional[str] = Field(None, max_length=50)
    modality: Optional[str] = Field(None, max_length=20)
    duration_months: Optional[int] = Field(None, gt=0)
    tuition_fee: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    entry_requirements: Optional[str] = None
    application_deadline: Optional[datetime] = None
    university_rank: Optional[int] = Field(None, gt=0)
    course_level: Optional[str] = Field(None, max_length=50)
    course_code: Optional[str] = Field(None, max_length=50)
    skill_ids: Optional[List[int]] = None
    career_outcome_ids: Optional[List[int]] = None


class Course(CourseBase):
    """Schema for course responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    skills: List[Skill] = []
    career_outcomes: List[CareerOutcome] = []
    
    class Config:
        from_attributes = True


class CourseList(BaseModel):
    """Schema for paginated course lists."""
    courses: List[Course]
    total: int
    page: int
    per_page: int
    pages: int