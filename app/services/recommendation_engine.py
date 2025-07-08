import math
from typing import List, Dict, Tuple, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.course import Course, Skill, CareerOutcome
from app.schemas.recommendation import RecommendationRequest, CourseMatch, RecommendationResponse


class CourseRecommendationEngine:
    """
    Core recommendation engine for matching users to suitable courses.
    Uses TF-IDF vectorization and cosine similarity for skill matching.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.skill_vectorizer = None
        self.course_skill_matrix = None
        self.courses_cache = []
        
    def initialize(self):
        """Initialize the recommendation engine with course data."""
        self._load_courses()
        self._build_skill_vectors()
        
    def _load_courses(self):
        """Load all courses from the database."""
        self.courses_cache = self.db.query(Course).all()
        
    def _build_skill_vectors(self):
        """Build TF-IDF vectors for course skills."""
        if not self.courses_cache:
            return
            
        # Create skill documents for each course
        course_skill_docs = []
        for course in self.courses_cache:
            # Combine skills and career outcomes as text documents
            skills_text = " ".join([skill.name.lower() for skill in course.skills])
            careers_text = " ".join([career.title.lower() for career in course.career_outcomes])
            
            # Also include course name and description for broader matching
            course_text = f"{course.name.lower()} {course.description or ''}".strip()
            
            # Combine all text
            full_doc = f"{skills_text} {careers_text} {course_text}"
            course_skill_docs.append(full_doc)
        
        if course_skill_docs:
            # Build TF-IDF matrix
            self.skill_vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2),
                lowercase=True
            )
            self.course_skill_matrix = self.skill_vectorizer.fit_transform(course_skill_docs)
    
    def get_recommendations(self, request: RecommendationRequest, limit: int = 20) -> RecommendationResponse:
        """
        Get course recommendations based on user preferences.
        
        Args:
            request: User preferences and requirements
            limit: Maximum number of recommendations to return
            
        Returns:
            RecommendationResponse with ranked course matches
        """
        if not self.courses_cache:
            self.initialize()
            
        if not self.courses_cache:
            return RecommendationResponse(
                recommendations=[],
                total_matches=0,
                search_metadata={"error": "No courses available"},
                suggestions=["Please ensure courses are loaded in the database"]
            )
        
        # Calculate scores for all courses
        course_scores = []
        user_query = self._build_user_query(request)
        
        for i, course in enumerate(self.courses_cache):
            score_data = self._calculate_course_score(course, request, user_query, i)
            if score_data['total_score'] > 0.1:  # Minimum threshold
                course_scores.append(score_data)
        
        # Sort by total score
        course_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Convert to CourseMatch objects
        recommendations = []
        for score_data in course_scores[:limit]:
            course_match = self._create_course_match(score_data)
            recommendations.append(course_match)
        
        # Generate search metadata and suggestions
        metadata = self._generate_search_metadata(request, course_scores)
        suggestions = self._generate_suggestions(request, course_scores)
        
        return RecommendationResponse(
            recommendations=recommendations,
            total_matches=len(course_scores),
            search_metadata=metadata,
            suggestions=suggestions
        )
    
    def _build_user_query(self, request: RecommendationRequest) -> str:
        """Build a query string from user input for TF-IDF matching."""
        query_parts = []
        
        if request.skills:
            query_parts.extend([skill.lower() for skill in request.skills])
        
        if request.interests:
            query_parts.extend([interest.lower() for interest in request.interests])
        
        if request.career_goals:
            query_parts.append(request.career_goals.lower())
            
        return " ".join(query_parts)
    
    def _calculate_course_score(self, course: Course, request: RecommendationRequest, 
                              user_query: str, course_index: int) -> Dict[str, Any]:
        """Calculate comprehensive matching score for a course."""
        
        # Skill/Interest similarity (TF-IDF)
        content_score = self._calculate_content_similarity(user_query, course_index)
        
        # Location matching
        location_score = self._calculate_location_score(course, request)
        
        # Career goals matching
        career_score = self._calculate_career_score(course, request)
        
        # Preference filtering
        filter_score = self._calculate_filter_score(course, request)
        
        # Calculate weighted total score
        total_score = (
            content_score * (request.skill_weight + request.interest_weight) +
            location_score * request.location_weight +
            career_score * request.career_weight
        ) * filter_score
        
        # Skill matches for explanation
        skill_matches = self._find_skill_matches(course, request.skills or [])
        
        return {
            'course': course,
            'total_score': total_score,
            'content_score': content_score,
            'location_score': location_score,
            'career_score': career_score,
            'filter_score': filter_score,
            'skill_matches': skill_matches
        }
    
    def _calculate_content_similarity(self, user_query: str, course_index: int) -> float:
        """Calculate TF-IDF cosine similarity between user query and course."""
        if not user_query or self.course_skill_matrix is None:
            return 0.0
            
        try:
            # Transform user query to TF-IDF vector
            user_vector = self.skill_vectorizer.transform([user_query])
            
            # Calculate cosine similarity
            course_vector = self.course_skill_matrix[course_index]
            similarity = cosine_similarity(user_vector, course_vector)[0][0]
            
            return float(similarity)
        except:
            return 0.0
    
    def _calculate_location_score(self, course: Course, request: RecommendationRequest) -> float:
        """Calculate location matching score."""
        if not request.location:
            return 1.0  # No preference = perfect match
            
        request_location = request.location.lower()
        
        # Check if it's an online course
        if course.modality and course.modality.lower() == 'online':
            return 1.0
        
        # Check city match
        if course.location_city and request_location in course.location_city.lower():
            return 1.0
            
        # Check country match
        if course.location_country and request_location in course.location_country.lower():
            return 0.7
            
        return 0.1  # No match but not completely incompatible
    
    def _calculate_career_score(self, course: Course, request: RecommendationRequest) -> float:
        """Calculate career goals matching score."""
        if not request.career_goals:
            return 1.0
            
        career_goals_lower = request.career_goals.lower()
        
        # Check against career outcomes
        for career_outcome in course.career_outcomes:
            if career_goals_lower in career_outcome.title.lower():
                return 1.0
            if career_outcome.description and career_goals_lower in career_outcome.description.lower():
                return 0.8
                
        # Check against course description
        if course.description and career_goals_lower in course.description.lower():
            return 0.6
            
        return 0.3  # Default partial match
    
    def _calculate_filter_score(self, course: Course, request: RecommendationRequest) -> float:
        """Apply hard filters and calculate compatibility score."""
        
        # Modality filter
        if request.modality and course.modality:
            if request.modality.lower() != course.modality.lower():
                return 0.0
        
        # Language filter
        if request.language_of_instruction:
            if course.language_of_instruction.lower() != request.language_of_instruction.lower():
                return 0.1
        
        # Tuition filter
        if request.max_tuition and course.tuition_fee:
            if course.tuition_fee > request.max_tuition:
                return 0.2  # Expensive but not impossible
        
        # Duration filter
        if request.max_duration_months and course.duration_months:
            if course.duration_months > request.max_duration_months:
                return 0.3
        
        # Course level filter
        if request.course_level and course.course_level:
            if request.course_level.lower() != course.course_level.lower():
                return 0.5
        
        return 1.0  # All filters passed
    
    def _find_skill_matches(self, course: Course, user_skills: List[str]) -> List[str]:
        """Find overlapping skills between user and course."""
        user_skills_lower = [skill.lower() for skill in user_skills]
        course_skills_lower = [skill.name.lower() for skill in course.skills]
        
        matches = []
        for user_skill in user_skills_lower:
            for course_skill in course_skills_lower:
                if user_skill in course_skill or course_skill in user_skill:
                    matches.append(course_skill.title())
                    break
        
        return list(set(matches))  # Remove duplicates
    
    def _create_course_match(self, score_data: Dict[str, Any]) -> CourseMatch:
        """Create a CourseMatch object from score data."""
        course = score_data['course']
        
        # Generate explanation
        explanation = self._generate_match_explanation(score_data)
        
        # Find missing requirements (simplified)
        missing_requirements = []
        if course.entry_requirements:
            # This is a simplified implementation
            # In a real system, you'd parse requirements more intelligently
            missing_requirements = ["Please check entry requirements"]
        
        return CourseMatch(
            course=course,
            match_score=score_data['total_score'],
            match_explanation=explanation,
            skill_matches=score_data['skill_matches'],
            skill_match_score=score_data['content_score'],
            interest_match_score=score_data['content_score'],  # Simplified
            location_match_score=score_data['location_score'],
            career_match_score=score_data['career_score'],
            missing_requirements=missing_requirements,
            similar_alternatives=[]  # Would be implemented with more data
        )
    
    def _generate_match_explanation(self, score_data: Dict[str, Any]) -> str:
        """Generate human-readable explanation for the match."""
        explanations = []
        
        skill_matches = score_data['skill_matches']
        if skill_matches:
            explanations.append(f"Matches {len(skill_matches)} of your skills: {', '.join(skill_matches[:3])}")
        
        if score_data['location_score'] > 0.8:
            explanations.append("Good location match")
        
        if score_data['career_score'] > 0.8:
            explanations.append("Aligns with your career goals")
        
        if score_data['content_score'] > 0.7:
            explanations.append("Strong content relevance")
        
        if not explanations:
            explanations.append("General compatibility based on your preferences")
        
        return ". ".join(explanations) + "."
    
    def _generate_search_metadata(self, request: RecommendationRequest, 
                                course_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate metadata about the search process."""
        return {
            "total_courses_analyzed": len(self.courses_cache),
            "query_skills_count": len(request.skills or []),
            "query_interests_count": len(request.interests or []),
            "average_match_score": np.mean([s['total_score'] for s in course_scores]) if course_scores else 0,
            "filters_applied": {
                "location": bool(request.location),
                "modality": bool(request.modality),
                "max_tuition": bool(request.max_tuition),
                "course_level": bool(request.course_level)
            }
        }
    
    def _generate_suggestions(self, request: RecommendationRequest, 
                            course_scores: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions for improving search results."""
        suggestions = []
        
        if len(course_scores) < 5:
            suggestions.append("Try expanding your location preferences or considering online courses")
        
        if not request.skills:
            suggestions.append("Add specific skills to get more targeted recommendations")
        
        if request.max_tuition and request.max_tuition < 10000:
            suggestions.append("Consider increasing your budget or looking for scholarship opportunities")
        
        if course_scores and np.mean([s['total_score'] for s in course_scores]) < 0.3:
            suggestions.append("Your criteria might be too specific. Try broadening your preferences")
        
        return suggestions