from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.course import Course


class RecommendationRequest(BaseModel):
    """Schema for course recommendation requests."""
    skills: Optional[List[str]] = Field([], description="List of skills the user has or wants to learn")
    interests: Optional[List[str]] = Field([], description="List of user interests")
    location: Optional[str] = Field(None, description="Preferred location (city, country)")
    modality: Optional[str] = Field(None, description="Preferred course modality (online, in-person, hybrid)")
    language_of_instruction: Optional[str] = Field("English", description="Preferred language of instruction")
    career_goals: Optional[str] = Field(None, description="Career goals or aspirations")
    academic_background: Optional[str] = Field(None, description="Academic background or level")
    time_horizon: Optional[str] = Field(None, description="When planning to start (this_year, next_year, flexible)")
    max_tuition: Optional[float] = Field(None, ge=0, description="Maximum tuition fee")
    course_level: Optional[str] = Field(None, description="Preferred course level (undergraduate, graduate, certificate)")
    max_duration_months: Optional[int] = Field(None, gt=0, description="Maximum course duration in months")
    university_rank_preference: Optional[str] = Field(None, description="University ranking preference (top_tier, mid_tier, any)")
    
    # Weighting preferences (0.0 to 1.0)
    skill_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for skill matching")
    interest_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for interest matching")
    location_weight: float = Field(0.15, ge=0.0, le=1.0, description="Weight for location preference")
    career_weight: float = Field(0.15, ge=0.0, le=1.0, description="Weight for career goals matching")


class CourseMatch(BaseModel):
    """Schema for individual course recommendation with match details."""
    course: Course
    match_score: float = Field(..., ge=0.0, le=1.0, description="Overall match score (0-1)")
    match_explanation: str = Field(..., description="Explanation of why this course matches")
    skill_matches: List[str] = Field([], description="Skills that matched with the course")
    skill_match_score: float = Field(0.0, ge=0.0, le=1.0, description="Skill-specific match score")
    interest_match_score: float = Field(0.0, ge=0.0, le=1.0, description="Interest-specific match score")
    location_match_score: float = Field(0.0, ge=0.0, le=1.0, description="Location-specific match score")
    career_match_score: float = Field(0.0, ge=0.0, le=1.0, description="Career goals match score")
    
    # Additional metadata
    missing_requirements: List[str] = Field([], description="Requirements the user might be missing")
    similar_alternatives: List[int] = Field([], description="IDs of similar course alternatives")


class RecommendationResponse(BaseModel):
    """Schema for course recommendation responses."""
    recommendations: List[CourseMatch] = Field(..., description="List of recommended courses")
    total_matches: int = Field(..., description="Total number of matching courses found")
    search_metadata: Dict[str, Any] = Field({}, description="Metadata about the search process")
    suggestions: List[str] = Field([], description="Suggestions for improving search results")
    
    class Config:
        from_attributes = True


class SkillExtractRequest(BaseModel):
    """Schema for skill extraction from free text."""
    text: str = Field(..., description="Free text to extract skills from")
    context: Optional[str] = Field(None, description="Additional context for skill extraction")


class SkillExtractResponse(BaseModel):
    """Schema for skill extraction response."""
    extracted_skills: List[str] = Field(..., description="List of extracted skills")
    confidence_scores: Dict[str, float] = Field({}, description="Confidence scores for each extracted skill")
    suggested_skills: List[str] = Field([], description="Additional suggested skills based on context")


class InterestExtractRequest(BaseModel):
    """Schema for interest extraction from free text."""
    text: str = Field(..., description="Free text to extract interests from")
    context: Optional[str] = Field(None, description="Additional context for interest extraction")


class InterestExtractResponse(BaseModel):
    """Schema for interest extraction response."""
    extracted_interests: List[str] = Field(..., description="List of extracted interests")
    confidence_scores: Dict[str, float] = Field({}, description="Confidence scores for each extracted interest")
    suggested_interests: List[str] = Field([], description="Additional suggested interests based on context")