import re
from typing import List, Dict, Tuple, Set
from collections import Counter
import spacy
from sqlalchemy.orm import Session

from app.models.course import Skill
from app.schemas.recommendation import SkillExtractRequest, SkillExtractResponse


class SkillExtractor:
    """
    NLP-based skill extraction service that identifies skills from free text.
    Uses spaCy for NLP processing and a database of known skills.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.nlp = None
        self.known_skills = set()
        self.skill_patterns = []
        
    def initialize(self):
        """Initialize the skill extractor with NLP model and skill database."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic processing if spaCy model not available
            self.nlp = None
            
        self._load_known_skills()
        self._create_skill_patterns()
    
    def _load_known_skills(self):
        """Load known skills from the database."""
        skills = self.db.query(Skill).all()
        self.known_skills = set(skill.name.lower() for skill in skills)
        
        # Add common technical skills that might not be in database
        common_skills = {
            'python', 'javascript', 'java', 'c++', 'html', 'css', 'sql', 'react',
            'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'docker',
            'kubernetes', 'aws', 'azure', 'git', 'machine learning', 'data analysis',
            'project management', 'communication', 'leadership', 'teamwork',
            'problem solving', 'critical thinking', 'creativity', 'adaptability'
        }
        self.known_skills.update(common_skills)
    
    def _create_skill_patterns(self):
        """Create regex patterns for skill extraction."""
        # Programming languages pattern
        programming_langs = r'\b(python|javascript|java|c\+\+|c#|ruby|go|rust|swift|kotlin|scala|r|matlab|php)\b'
        
        # Framework/library patterns
        frameworks = r'\b(react|angular|vue|django|flask|spring|express|laravel|rails|tensorflow|pytorch|scikit-learn)\b'
        
        # Database patterns
        databases = r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|cassandra|oracle)\b'
        
        # Cloud/DevOps patterns
        cloud_devops = r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible|git|gitlab|github)\b'
        
        # Soft skills patterns
        soft_skills = r'\b(leadership|communication|teamwork|project\s+management|problem\s+solving|critical\s+thinking|creativity|adaptability|time\s+management)\b'
        
        self.skill_patterns = [
            (programming_langs, 'technical'),
            (frameworks, 'technical'),
            (databases, 'technical'),
            (cloud_devops, 'technical'),
            (soft_skills, 'soft')
        ]
    
    def extract_skills(self, request: SkillExtractRequest) -> SkillExtractResponse:
        """
        Extract skills from free text using NLP and pattern matching.
        
        Args:
            request: Text and context for skill extraction
            
        Returns:
            SkillExtractResponse with extracted skills and confidence scores
        """
        if not self.known_skills:
            self.initialize()
        
        text = request.text.lower()
        extracted_skills = set()
        confidence_scores = {}
        
        # Method 1: Direct matching against known skills
        direct_matches = self._extract_direct_matches(text)
        extracted_skills.update(direct_matches.keys())
        confidence_scores.update(direct_matches)
        
        # Method 2: Pattern-based extraction
        pattern_matches = self._extract_pattern_matches(text)
        extracted_skills.update(pattern_matches.keys())
        confidence_scores.update(pattern_matches)
        
        # Method 3: NLP-based extraction (if spaCy available)
        if self.nlp:
            nlp_matches = self._extract_nlp_matches(text)
            extracted_skills.update(nlp_matches.keys())
            confidence_scores.update(nlp_matches)
        
        # Method 4: Context-based suggestions
        context_skills = self._extract_context_skills(text, request.context)
        
        # Convert to lists and filter
        final_skills = list(extracted_skills)
        final_confidence = {skill: confidence_scores.get(skill, 0.5) for skill in final_skills}
        
        return SkillExtractResponse(
            extracted_skills=final_skills,
            confidence_scores=final_confidence,
            suggested_skills=context_skills
        )
    
    def _extract_direct_matches(self, text: str) -> Dict[str, float]:
        """Extract skills by direct string matching against known skills."""
        matches = {}
        
        for skill in self.known_skills:
            # Exact match
            if skill in text:
                # Higher confidence for longer, more specific skills
                confidence = min(0.9, 0.5 + len(skill) * 0.02)
                matches[skill] = confidence
        
        return matches
    
    def _extract_pattern_matches(self, text: str) -> Dict[str, float]:
        """Extract skills using regex patterns."""
        matches = {}
        
        for pattern, category in self.skill_patterns:
            found_skills = re.findall(pattern, text, re.IGNORECASE)
            for skill in found_skills:
                skill_clean = skill.lower().strip()
                if skill_clean:
                    # Pattern matches get medium confidence
                    matches[skill_clean] = 0.7
        
        return matches
    
    def _extract_nlp_matches(self, text: str) -> Dict[str, float]:
        """Extract skills using spaCy NLP processing."""
        matches = {}
        
        try:
            doc = self.nlp(text)
            
            # Extract named entities that might be skills
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'WORK_OF_ART']:
                    skill_candidate = ent.text.lower().strip()
                    if self._is_likely_skill(skill_candidate):
                        matches[skill_candidate] = 0.6
            
            # Extract noun phrases that might be skills
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.lower().strip()
                if self._is_likely_skill(chunk_text) and len(chunk_text.split()) <= 3:
                    matches[chunk_text] = 0.5
        
        except Exception:
            # Fallback if NLP processing fails
            pass
        
        return matches
    
    def _extract_context_skills(self, text: str, context: str = None) -> List[str]:
        """Extract additional skill suggestions based on context."""
        suggestions = []
        
        # Domain-specific skill suggestions
        if any(word in text for word in ['data', 'analytics', 'science', 'machine learning']):
            suggestions.extend(['python', 'sql', 'statistics', 'machine learning', 'data visualization'])
        
        if any(word in text for word in ['web', 'frontend', 'ui', 'ux']):
            suggestions.extend(['html', 'css', 'javascript', 'react', 'user experience design'])
        
        if any(word in text for word in ['backend', 'server', 'api']):
            suggestions.extend(['python', 'java', 'sql', 'rest api', 'database design'])
        
        if any(word in text for word in ['mobile', 'app', 'ios', 'android']):
            suggestions.extend(['swift', 'kotlin', 'react native', 'mobile development'])
        
        if any(word in text for word in ['cloud', 'devops', 'deployment']):
            suggestions.extend(['aws', 'docker', 'kubernetes', 'ci/cd', 'linux'])
        
        if any(word in text for word in ['management', 'team', 'project']):
            suggestions.extend(['project management', 'leadership', 'communication', 'agile'])
        
        # Remove duplicates and return
        return list(set(suggestions))
    
    def _is_likely_skill(self, text: str) -> bool:
        """Determine if a text fragment is likely to be a skill."""
        # Filter out common non-skill words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'a', 'an', 'as', 'are',
            'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
        
        # Basic filtering
        if text in stop_words:
            return False
        
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Contains only letters, numbers, spaces, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\+\#\.\-]+$', text):
            return False
        
        # Additional heuristics
        if any(keyword in text for keyword in ['skill', 'technology', 'language', 'framework']):
            return True
        
        if text in self.known_skills:
            return True
        
        # If it looks like a technology name (contains version numbers, etc.)
        if re.search(r'\d+', text) and any(tech in text for tech in ['js', 'css', 'html', 'api']):
            return True
        
        return len(text.split()) <= 3  # Prefer shorter phrases


def get_skill_suggestions() -> List[str]:
    """Get a list of common skill suggestions for auto-completion."""
    return [
        # Programming Languages
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin',
        
        # Web Technologies
        'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Express.js', 'REST API',
        
        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch',
        
        # Cloud & DevOps
        'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'Git',
        
        # Data & AI
        'Machine Learning', 'Data Analysis', 'Statistics', 'TensorFlow', 'PyTorch', 'Pandas',
        
        # Soft Skills
        'Leadership', 'Communication', 'Project Management', 'Teamwork', 'Problem Solving',
        'Critical Thinking', 'Creativity', 'Adaptability', 'Time Management',
        
        # Design
        'UI/UX Design', 'Graphic Design', 'Photoshop', 'Figma', 'User Research',
        
        # Business
        'Business Analysis', 'Strategic Planning', 'Market Research', 'Sales', 'Marketing'
    ]