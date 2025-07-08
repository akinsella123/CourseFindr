#!/usr/bin/env python3
"""
CourseMatch Database Initialization Script

This script initializes the database with sample data for testing and development.
Run this after setting up the database to populate it with example courses.
"""

import os
import sys
import csv
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.models.course import Course, Skill, CareerOutcome


def init_database():
    """Initialize database tables."""
    print("Creating database tables...")
    create_tables()
    print("✓ Database tables created")


def load_sample_data():
    """Load sample course data from CSV file."""
    db = SessionLocal()
    
    try:
        # Path to sample data
        csv_path = project_root / "data" / "sample_courses.csv"
        
        if not csv_path.exists():
            print(f"❌ Sample data file not found: {csv_path}")
            return
        
        print(f"Loading sample data from {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            courses_added = 0
            skills_added = 0
            outcomes_added = 0
            
            for row in reader:
                try:
                    # Create course
                    course_data = {
                        'name': row['name'],
                        'description': row['description'],
                        'institution': row['institution'],
                        'location_city': row.get('location_city'),
                        'location_country': row.get('location_country'),
                        'modality': row.get('modality', 'in-person'),
                        'language_of_instruction': 'English',
                        'course_level': row.get('course_level'),
                        'entry_requirements': row.get('entry_requirements')
                    }
                    
                    # Handle numeric fields
                    if row.get('duration_months'):
                        course_data['duration_months'] = int(row['duration_months'])
                    
                    if row.get('tuition_fee'):
                        course_data['tuition_fee'] = float(row['tuition_fee'])
                    
                    if row.get('currency'):
                        course_data['currency'] = row['currency']
                    
                    # Create course
                    course = Course(**course_data)
                    
                    # Handle skills
                    if row.get('skills'):
                        skill_names = [s.strip() for s in row['skills'].split(';')]
                        skills = []
                        
                        for skill_name in skill_names:
                            if skill_name:
                                # Check if skill exists
                                skill = db.query(Skill).filter(Skill.name == skill_name).first()
                                if not skill:
                                    # Create new skill
                                    skill = Skill(
                                        name=skill_name,
                                        category='technical' if any(tech in skill_name.lower() 
                                                                  for tech in ['python', 'java', 'sql', 'html', 'css']) 
                                               else 'general'
                                    )
                                    db.add(skill)
                                    db.flush()
                                    skills_added += 1
                                
                                skills.append(skill)
                        
                        course.skills = skills
                    
                    # Handle career outcomes
                    if row.get('career_outcomes'):
                        outcome_names = [o.strip() for o in row['career_outcomes'].split(';')]
                        outcomes = []
                        
                        for outcome_name in outcome_names:
                            if outcome_name:
                                # Check if career outcome exists
                                outcome = db.query(CareerOutcome).filter(
                                    CareerOutcome.title == outcome_name
                                ).first()
                                
                                if not outcome:
                                    # Create new career outcome
                                    outcome = CareerOutcome(title=outcome_name)
                                    db.add(outcome)
                                    db.flush()
                                    outcomes_added += 1
                                
                                outcomes.append(outcome)
                        
                        course.career_outcomes = outcomes
                    
                    db.add(course)
                    courses_added += 1
                    
                except Exception as e:
                    print(f"❌ Error processing course '{row.get('name', 'Unknown')}': {e}")
                    continue
            
            # Commit all changes
            db.commit()
            
            print(f"✓ Successfully loaded sample data:")
            print(f"  - {courses_added} courses")
            print(f"  - {skills_added} skills")
            print(f"  - {outcomes_added} career outcomes")
            
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        db.rollback()
    finally:
        db.close()


def verify_data():
    """Verify that data was loaded correctly."""
    db = SessionLocal()
    
    try:
        course_count = db.query(Course).count()
        skill_count = db.query(Skill).count()
        outcome_count = db.query(CareerOutcome).count()
        
        print(f"\nDatabase verification:")
        print(f"  - Total courses: {course_count}")
        print(f"  - Total skills: {skill_count}")
        print(f"  - Total career outcomes: {outcome_count}")
        
        if course_count > 0:
            # Show sample course
            sample_course = db.query(Course).first()
            print(f"\nSample course: '{sample_course.name}' by {sample_course.institution}")
            print(f"  - Skills: {len(sample_course.skills)}")
            print(f"  - Career outcomes: {len(sample_course.career_outcomes)}")
        
        return course_count > 0
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False
    finally:
        db.close()


def main():
    """Main initialization function."""
    print("🚀 Initializing CourseMatch database...")
    print("=" * 50)
    
    # Step 1: Initialize database
    init_database()
    
    # Step 2: Load sample data
    load_sample_data()
    
    # Step 3: Verify data
    success = verify_data()
    
    print("=" * 50)
    if success:
        print("✅ Initialization completed successfully!")
        print("\nNext steps:")
        print("1. Start the application: uvicorn app.main:app --reload")
        print("2. Visit the API docs: http://localhost:8000/docs")
        print("3. Try the recommendation endpoint with sample data")
    else:
        print("❌ Initialization failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()