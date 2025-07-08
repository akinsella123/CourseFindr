from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for many-to-many relationship between courses and skills
course_skills = Table(
    'course_skills',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)

# Association table for many-to-many relationship between courses and career outcomes
course_career_outcomes = Table(
    'course_career_outcomes',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('career_outcome_id', Integer, ForeignKey('career_outcomes.id'), primary_key=True)
)


class Course(Base):
    """Course model representing university courses."""
    
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    institution = Column(String(255), nullable=False, index=True)
    
    # Location and delivery
    location_city = Column(String(100), nullable=True, index=True)
    location_country = Column(String(100), nullable=True, index=True)
    language_of_instruction = Column(String(50), nullable=False, default="English")
    modality = Column(String(20), nullable=False, default="in-person")  # online, in-person, hybrid
    
    # Course details
    duration_months = Column(Integer, nullable=True)
    tuition_fee = Column(Float, nullable=True)
    currency = Column(String(3), nullable=True, default="USD")
    
    # Requirements and deadlines
    entry_requirements = Column(Text, nullable=True)
    application_deadline = Column(DateTime, nullable=True)
    
    # Additional metadata
    university_rank = Column(Integer, nullable=True)
    course_level = Column(String(50), nullable=True)  # undergraduate, graduate, certificate
    course_code = Column(String(50), nullable=True, unique=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    skills = relationship("Skill", secondary=course_skills, back_populates="courses")
    career_outcomes = relationship("CareerOutcome", secondary=course_career_outcomes, back_populates="courses")
    
    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}', institution='{self.institution}')>"


class Skill(Base):
    """Skill model representing skills taught in courses."""
    
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=True)  # technical, soft, domain-specific
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    courses = relationship("Course", secondary=course_skills, back_populates="skills")
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"


class CareerOutcome(Base):
    """Career outcome model representing typical career paths after course completion."""
    
    __tablename__ = "career_outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    average_salary = Column(Float, nullable=True)
    salary_currency = Column(String(3), nullable=True, default="USD")
    employment_rate = Column(Float, nullable=True)  # percentage
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    courses = relationship("Course", secondary=course_career_outcomes, back_populates="career_outcomes")
    
    def __repr__(self):
        return f"<CareerOutcome(id={self.id}, title='{self.title}')>"