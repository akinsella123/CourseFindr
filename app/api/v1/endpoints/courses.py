from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import csv
import io

from app.core.database import get_db
from app.models.course import Course, Skill, CareerOutcome
from app.schemas.course import (
    Course as CourseSchema,
    CourseCreate,
    CourseUpdate,
    CourseList,
    Skill as SkillSchema,
    SkillCreate,
    CareerOutcome as CareerOutcomeSchema,
    CareerOutcomeCreate
)

router = APIRouter()


@router.get("/", response_model=CourseList)
async def get_courses(
    skip: int = Query(0, ge=0, description="Number of courses to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of courses to return"),
    search: Optional[str] = Query(None, description="Search term for course name or description"),
    institution: Optional[str] = Query(None, description="Filter by institution"),
    location_country: Optional[str] = Query(None, description="Filter by country"),
    modality: Optional[str] = Query(None, description="Filter by modality"),
    course_level: Optional[str] = Query(None, description="Filter by course level"),
    max_tuition: Optional[float] = Query(None, ge=0, description="Maximum tuition fee"),
    db: Session = Depends(get_db)
):
    """
    Get a list of courses with optional filtering and pagination.
    
    Supports filtering by various criteria and full-text search.
    """
    try:
        # Build query
        query = db.query(Course)
        
        # Apply filters
        if search:
            search_filter = or_(
                Course.name.ilike(f"%{search}%"),
                Course.description.ilike(f"%{search}%"),
                Course.institution.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if institution:
            query = query.filter(Course.institution.ilike(f"%{institution}%"))
        
        if location_country:
            query = query.filter(Course.location_country.ilike(f"%{location_country}%"))
        
        if modality:
            query = query.filter(Course.modality == modality)
        
        if course_level:
            query = query.filter(Course.course_level == course_level)
        
        if max_tuition:
            query = query.filter(
                or_(Course.tuition_fee.is_(None), Course.tuition_fee <= max_tuition)
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        courses = query.offset(skip).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        return CourseList(
            courses=courses,
            total=total,
            page=page,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving courses: {str(e)}"
        )


@router.get("/{course_id}", response_model=CourseSchema)
async def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get a specific course by ID."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/", response_model=CourseSchema)
async def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """
    Create a new course.
    
    Admin functionality for adding courses to the database.
    """
    try:
        # Create course object
        db_course = Course(**course.dict(exclude={"skill_ids", "career_outcome_ids"}))
        
        # Add skills
        if course.skill_ids:
            skills = db.query(Skill).filter(Skill.id.in_(course.skill_ids)).all()
            db_course.skills = skills
        
        # Add career outcomes
        if course.career_outcome_ids:
            outcomes = db.query(CareerOutcome).filter(
                CareerOutcome.id.in_(course.career_outcome_ids)
            ).all()
            db_course.career_outcomes = outcomes
        
        # Save to database
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        
        return db_course
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating course: {str(e)}"
        )


@router.put("/{course_id}", response_model=CourseSchema)
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing course."""
    try:
        # Get existing course
        db_course = db.query(Course).filter(Course.id == course_id).first()
        if not db_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Update fields
        update_data = course_update.dict(exclude_unset=True, exclude={"skill_ids", "career_outcome_ids"})
        for field, value in update_data.items():
            setattr(db_course, field, value)
        
        # Update skills if provided
        if course_update.skill_ids is not None:
            skills = db.query(Skill).filter(Skill.id.in_(course_update.skill_ids)).all()
            db_course.skills = skills
        
        # Update career outcomes if provided
        if course_update.career_outcome_ids is not None:
            outcomes = db.query(CareerOutcome).filter(
                CareerOutcome.id.in_(course_update.career_outcome_ids)
            ).all()
            db_course.career_outcomes = outcomes
        
        db.commit()
        db.refresh(db_course)
        
        return db_course
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating course: {str(e)}"
        )


@router.delete("/{course_id}")
async def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course."""
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        db.delete(course)
        db.commit()
        
        return {"message": "Course deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting course: {str(e)}"
        )


@router.post("/upload-csv")
async def upload_courses_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload courses from a CSV file.
    
    Expected CSV format:
    name,description,institution,location_city,location_country,modality,duration_months,tuition_fee,currency,course_level,skills,career_outcomes
    
    Skills and career outcomes should be semicolon-separated.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        courses_created = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
            try:
                # Create course data
                course_data = {}
                
                # Required fields
                required_fields = ['name', 'institution']
                for field in required_fields:
                    if not row.get(field):
                        errors.append(f"Row {row_num}: Missing required field '{field}'")
                        continue
                    course_data[field] = row[field].strip()
                
                # Optional fields
                optional_fields = [
                    'description', 'location_city', 'location_country',
                    'modality', 'currency', 'course_level', 'entry_requirements'
                ]
                for field in optional_fields:
                    if row.get(field):
                        course_data[field] = row[field].strip()
                
                # Numeric fields
                if row.get('duration_months'):
                    try:
                        course_data['duration_months'] = int(row['duration_months'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid duration_months")
                        continue
                
                if row.get('tuition_fee'):
                    try:
                        course_data['tuition_fee'] = float(row['tuition_fee'])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid tuition_fee")
                        continue
                
                # Create course
                db_course = Course(**course_data)
                
                # Handle skills
                if row.get('skills'):
                    skill_names = [s.strip() for s in row['skills'].split(';') if s.strip()]
                    skills = []
                    for skill_name in skill_names:
                        skill = db.query(Skill).filter(Skill.name == skill_name).first()
                        if not skill:
                            # Create skill if it doesn't exist
                            skill = Skill(name=skill_name, category='general')
                            db.add(skill)
                            db.flush()  # Get the ID
                        skills.append(skill)
                    db_course.skills = skills
                
                # Handle career outcomes
                if row.get('career_outcomes'):
                    outcome_names = [o.strip() for o in row['career_outcomes'].split(';') if o.strip()]
                    outcomes = []
                    for outcome_name in outcome_names:
                        outcome = db.query(CareerOutcome).filter(CareerOutcome.title == outcome_name).first()
                        if not outcome:
                            # Create career outcome if it doesn't exist
                            outcome = CareerOutcome(title=outcome_name)
                            db.add(outcome)
                            db.flush()  # Get the ID
                        outcomes.append(outcome)
                    db_course.career_outcomes = outcomes
                
                db.add(db_course)
                courses_created += 1
                
            except Exception as row_error:
                errors.append(f"Row {row_num}: {str(row_error)}")
        
        # Commit all changes
        db.commit()
        
        return {
            "message": f"Successfully uploaded {courses_created} courses",
            "courses_created": courses_created,
            "errors": errors[:10]  # Limit error messages
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading CSV: {str(e)}"
        )


@router.get("/export/csv")
async def export_courses_csv(
    search: Optional[str] = None,
    institution: Optional[str] = None,
    location_country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export courses to CSV format.
    
    Supports the same filtering options as the get_courses endpoint.
    """
    try:
        # Build query with same filters as get_courses
        query = db.query(Course)
        
        if search:
            search_filter = or_(
                Course.name.ilike(f"%{search}%"),
                Course.description.ilike(f"%{search}%"),
                Course.institution.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if institution:
            query = query.filter(Course.institution.ilike(f"%{institution}%"))
        
        if location_country:
            query = query.filter(Course.location_country.ilike(f"%{location_country}%"))
        
        courses = query.all()
        
        # Generate CSV content
        csv_content = io.StringIO()
        fieldnames = [
            'id', 'name', 'description', 'institution', 'location_city',
            'location_country', 'modality', 'duration_months', 'tuition_fee',
            'currency', 'course_level', 'skills', 'career_outcomes'
        ]
        
        writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
        writer.writeheader()
        
        for course in courses:
            row = {
                'id': course.id,
                'name': course.name,
                'description': course.description or '',
                'institution': course.institution,
                'location_city': course.location_city or '',
                'location_country': course.location_country or '',
                'modality': course.modality or '',
                'duration_months': course.duration_months or '',
                'tuition_fee': course.tuition_fee or '',
                'currency': course.currency or '',
                'course_level': course.course_level or '',
                'skills': ';'.join([skill.name for skill in course.skills]),
                'career_outcomes': ';'.join([outcome.title for outcome in course.career_outcomes])
            }
            writer.writerow(row)
        
        # Return CSV as download
        from fastapi.responses import StreamingResponse
        csv_content.seek(0)
        
        return StreamingResponse(
            io.BytesIO(csv_content.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=courses.csv"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting CSV: {str(e)}"
        )