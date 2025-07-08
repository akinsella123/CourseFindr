from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import tempfile
import os

from app.core.database import get_db
from app.services.recommendation_engine import CourseRecommendationEngine
from app.services.skill_extractor import SkillExtractor
from app.services.pdf_generator import PDFGenerator
from app.schemas.recommendation import (
    RecommendationRequest, 
    RecommendationResponse,
    SkillExtractRequest,
    SkillExtractResponse,
    InterestExtractRequest,
    InterestExtractResponse
)

router = APIRouter()


@router.post("/recommend", response_model=RecommendationResponse)
async def get_course_recommendations(
    request: RecommendationRequest,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get personalized course recommendations based on user preferences.
    
    - **skills**: List of skills the user has or wants to learn
    - **interests**: List of user interests
    - **location**: Preferred location (city, country, or "online")
    - **career_goals**: Career aspirations or goals
    - **modality**: Preferred delivery method (online, in-person, hybrid)
    - **max_tuition**: Maximum tuition budget
    - **course_level**: Preferred academic level
    - **limit**: Maximum number of recommendations to return (default: 20)
    
    Returns a ranked list of course recommendations with match explanations.
    """
    try:
        # Initialize recommendation engine
        engine = CourseRecommendationEngine(db)
        
        # Get recommendations
        recommendations = engine.get_recommendations(request, limit=limit)
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.post("/recommend/export", response_class=FileResponse)
async def export_recommendations_pdf(
    request: RecommendationRequest,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Generate and download a PDF report of course recommendations.
    
    Takes the same parameters as the recommend endpoint but returns a PDF file.
    """
    try:
        # Get recommendations
        engine = CourseRecommendationEngine(db)
        recommendations = engine.get_recommendations(request, limit=limit)
        
        # Generate PDF
        pdf_generator = PDFGenerator()
        pdf_content = pdf_generator.generate_recommendations_pdf(
            recommendations,
            user_query=request.dict()
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
        
        # Return file response
        return FileResponse(
            path=tmp_file_path,
            filename="course_recommendations.pdf",
            media_type="application/pdf",
            background=lambda: os.unlink(tmp_file_path)  # Clean up temp file
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )


@router.post("/extract-skills", response_model=SkillExtractResponse)
async def extract_skills_from_text(
    request: SkillExtractRequest,
    db: Session = Depends(get_db)
):
    """
    Extract skills from free text using NLP.
    
    - **text**: Free text containing skill descriptions
    - **context**: Optional context to improve extraction accuracy
    
    Returns extracted skills with confidence scores and suggestions.
    """
    try:
        extractor = SkillExtractor(db)
        result = extractor.extract_skills(request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting skills: {str(e)}"
        )


@router.post("/extract-interests", response_model=InterestExtractResponse)
async def extract_interests_from_text(
    request: InterestExtractRequest,
    db: Session = Depends(get_db)
):
    """
    Extract interests from free text using NLP.
    
    - **text**: Free text containing interest descriptions
    - **context**: Optional context to improve extraction accuracy
    
    Returns extracted interests with confidence scores and suggestions.
    """
    try:
        # For now, we'll reuse the skill extractor for interests
        # In a real implementation, you might want a separate interest extractor
        extractor = SkillExtractor(db)
        
        # Convert to skill extract request
        skill_request = SkillExtractRequest(
            text=request.text,
            context=request.context
        )
        
        skill_result = extractor.extract_skills(skill_request)
        
        # Convert result to interest response
        # Filter for more general/interest-like terms
        interests = [
            skill for skill in skill_result.extracted_skills
            if any(word in skill.lower() for word in [
                'design', 'art', 'music', 'business', 'science', 'research',
                'education', 'health', 'finance', 'marketing', 'writing',
                'communication', 'environment', 'sustainability', 'innovation'
            ])
        ]
        
        return InterestExtractResponse(
            extracted_interests=interests,
            confidence_scores={
                interest: skill_result.confidence_scores.get(interest, 0.5)
                for interest in interests
            },
            suggested_interests=skill_result.suggested_skills[:5]  # Limit suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting interests: {str(e)}"
        )


@router.get("/search-suggestions")
async def get_search_suggestions(
    query: str = "",
    type: str = "skills",  # skills, interests, locations
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get search suggestions for auto-completion.
    
    - **query**: Partial search term
    - **type**: Type of suggestions (skills, interests, locations)
    - **limit**: Maximum number of suggestions
    
    Returns a list of matching suggestions.
    """
    try:
        suggestions = []
        query_lower = query.lower()
        
        if type == "skills":
            from app.services.skill_extractor import get_skill_suggestions
            all_skills = get_skill_suggestions()
            suggestions = [
                skill for skill in all_skills
                if query_lower in skill.lower()
            ][:limit]
            
        elif type == "interests":
            # Common interest categories
            common_interests = [
                "Technology", "Business", "Arts", "Science", "Health", "Education",
                "Environment", "Finance", "Marketing", "Design", "Music", "Sports",
                "Travel", "Writing", "Research", "Innovation", "Sustainability",
                "Social Impact", "Gaming", "Photography", "Cooking", "Fashion"
            ]
            suggestions = [
                interest for interest in common_interests
                if query_lower in interest.lower()
            ][:limit]
            
        elif type == "locations":
            # Common locations/countries
            common_locations = [
                "United States", "United Kingdom", "Canada", "Australia", "Germany",
                "France", "Netherlands", "Sweden", "Singapore", "Japan", "Online",
                "New York", "London", "Toronto", "Sydney", "Berlin", "Amsterdam",
                "Stockholm", "Tokyo", "Remote", "Hybrid"
            ]
            suggestions = [
                location for location in common_locations
                if query_lower in location.lower()
            ][:limit]
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting suggestions: {str(e)}"
        )


@router.get("/recommendation-stats")
async def get_recommendation_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the recommendation system.
    
    Returns information about available courses, skills, and system performance.
    """
    try:
        from app.models.course import Course, Skill, CareerOutcome
        
        # Get basic counts
        total_courses = db.query(Course).count()
        total_skills = db.query(Skill).count()
        total_career_outcomes = db.query(CareerOutcome).count()
        
        # Get distribution by modality
        modality_stats = db.query(Course.modality, db.func.count(Course.id))\
                           .group_by(Course.modality)\
                           .all()
        
        # Get distribution by level
        level_stats = db.query(Course.course_level, db.func.count(Course.id))\
                        .filter(Course.course_level.isnot(None))\
                        .group_by(Course.course_level)\
                        .all()
        
        # Get distribution by country
        country_stats = db.query(Course.location_country, db.func.count(Course.id))\
                         .filter(Course.location_country.isnot(None))\
                         .group_by(Course.location_country)\
                         .limit(10)\
                         .all()
        
        return {
            "total_courses": total_courses,
            "total_skills": total_skills,
            "total_career_outcomes": total_career_outcomes,
            "modality_distribution": dict(modality_stats),
            "level_distribution": dict(level_stats),
            "top_countries": dict(country_stats),
            "system_status": "operational"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )