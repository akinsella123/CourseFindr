from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.course import Skill, CareerOutcome
from app.schemas.course import (
    Skill as SkillSchema,
    SkillCreate,
    CareerOutcome as CareerOutcomeSchema,
    CareerOutcomeCreate
)

router = APIRouter()


# Skills endpoints
@router.get("/skills", response_model=List[SkillSchema])
async def get_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search skills by name"),
    category: Optional[str] = Query(None, description="Filter by skill category"),
    db: Session = Depends(get_db)
):
    """
    Get a list of all available skills with optional filtering.
    
    Used for auto-completion and skill selection in the frontend.
    """
    try:
        query = db.query(Skill)
        
        if search:
            query = query.filter(Skill.name.ilike(f"%{search}%"))
        
        if category:
            query = query.filter(Skill.category == category)
        
        skills = query.offset(skip).limit(limit).all()
        return skills
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving skills: {str(e)}"
        )


@router.post("/skills", response_model=SkillSchema)
async def create_skill(skill: SkillCreate, db: Session = Depends(get_db)):
    """Create a new skill."""
    try:
        # Check if skill already exists
        existing_skill = db.query(Skill).filter(
            Skill.name.ilike(skill.name)
        ).first()
        
        if existing_skill:
            raise HTTPException(
                status_code=400,
                detail="Skill with this name already exists"
            )
        
        db_skill = Skill(**skill.dict())
        db.add(db_skill)
        db.commit()
        db.refresh(db_skill)
        
        return db_skill
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating skill: {str(e)}"
        )


@router.get("/skills/{skill_id}", response_model=SkillSchema)
async def get_skill(skill_id: int, db: Session = Depends(get_db)):
    """Get a specific skill by ID."""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/skills/{skill_id}", response_model=SkillSchema)
async def update_skill(
    skill_id: int,
    skill_update: SkillCreate,
    db: Session = Depends(get_db)
):
    """Update an existing skill."""
    try:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Check for name conflicts
        if skill_update.name != skill.name:
            existing_skill = db.query(Skill).filter(
                Skill.name.ilike(skill_update.name),
                Skill.id != skill_id
            ).first()
            
            if existing_skill:
                raise HTTPException(
                    status_code=400,
                    detail="Skill with this name already exists"
                )
        
        # Update fields
        for field, value in skill_update.dict().items():
            setattr(skill, field, value)
        
        db.commit()
        db.refresh(skill)
        
        return skill
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating skill: {str(e)}"
        )


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    """Delete a skill."""
    try:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        db.delete(skill)
        db.commit()
        
        return {"message": "Skill deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting skill: {str(e)}"
        )


# Career outcomes endpoints
@router.get("/career-outcomes", response_model=List[CareerOutcomeSchema])
async def get_career_outcomes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search career outcomes by title"),
    db: Session = Depends(get_db)
):
    """Get a list of all career outcomes."""
    try:
        query = db.query(CareerOutcome)
        
        if search:
            query = query.filter(
                or_(
                    CareerOutcome.title.ilike(f"%{search}%"),
                    CareerOutcome.description.ilike(f"%{search}%")
                )
            )
        
        outcomes = query.offset(skip).limit(limit).all()
        return outcomes
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving career outcomes: {str(e)}"
        )


@router.post("/career-outcomes", response_model=CareerOutcomeSchema)
async def create_career_outcome(
    outcome: CareerOutcomeCreate,
    db: Session = Depends(get_db)
):
    """Create a new career outcome."""
    try:
        # Check if career outcome already exists
        existing_outcome = db.query(CareerOutcome).filter(
            CareerOutcome.title.ilike(outcome.title)
        ).first()
        
        if existing_outcome:
            raise HTTPException(
                status_code=400,
                detail="Career outcome with this title already exists"
            )
        
        db_outcome = CareerOutcome(**outcome.dict())
        db.add(db_outcome)
        db.commit()
        db.refresh(db_outcome)
        
        return db_outcome
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating career outcome: {str(e)}"
        )


@router.get("/career-outcomes/{outcome_id}", response_model=CareerOutcomeSchema)
async def get_career_outcome(outcome_id: int, db: Session = Depends(get_db)):
    """Get a specific career outcome by ID."""
    outcome = db.query(CareerOutcome).filter(CareerOutcome.id == outcome_id).first()
    if not outcome:
        raise HTTPException(status_code=404, detail="Career outcome not found")
    return outcome


@router.put("/career-outcomes/{outcome_id}", response_model=CareerOutcomeSchema)
async def update_career_outcome(
    outcome_id: int,
    outcome_update: CareerOutcomeCreate,
    db: Session = Depends(get_db)
):
    """Update an existing career outcome."""
    try:
        outcome = db.query(CareerOutcome).filter(CareerOutcome.id == outcome_id).first()
        if not outcome:
            raise HTTPException(status_code=404, detail="Career outcome not found")
        
        # Check for title conflicts
        if outcome_update.title != outcome.title:
            existing_outcome = db.query(CareerOutcome).filter(
                CareerOutcome.title.ilike(outcome_update.title),
                CareerOutcome.id != outcome_id
            ).first()
            
            if existing_outcome:
                raise HTTPException(
                    status_code=400,
                    detail="Career outcome with this title already exists"
                )
        
        # Update fields
        for field, value in outcome_update.dict().items():
            setattr(outcome, field, value)
        
        db.commit()
        db.refresh(outcome)
        
        return outcome
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating career outcome: {str(e)}"
        )


@router.delete("/career-outcomes/{outcome_id}")
async def delete_career_outcome(outcome_id: int, db: Session = Depends(get_db)):
    """Delete a career outcome."""
    try:
        outcome = db.query(CareerOutcome).filter(CareerOutcome.id == outcome_id).first()
        if not outcome:
            raise HTTPException(status_code=404, detail="Career outcome not found")
        
        db.delete(outcome)
        db.commit()
        
        return {"message": "Career outcome deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting career outcome: {str(e)}"
        )


@router.get("/skill-categories")
async def get_skill_categories(db: Session = Depends(get_db)):
    """Get list of all skill categories."""
    try:
        categories = db.query(Skill.category).distinct().filter(
            Skill.category.isnot(None)
        ).all()
        
        return {
            "categories": [cat[0] for cat in categories if cat[0]]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving skill categories: {str(e)}"
        )


@router.get("/popular-skills")
async def get_popular_skills(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most popular skills (by course count)."""
    try:
        from app.models.course import course_skills
        
        # Query skills with course count
        popular_skills = db.query(
            Skill.id,
            Skill.name,
            Skill.category,
            db.func.count(course_skills.c.course_id).label('course_count')
        ).join(
            course_skills, Skill.id == course_skills.c.skill_id
        ).group_by(
            Skill.id, Skill.name, Skill.category
        ).order_by(
            db.func.count(course_skills.c.course_id).desc()
        ).limit(limit).all()
        
        return {
            "popular_skills": [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "category": skill.category,
                    "course_count": skill.course_count
                }
                for skill in popular_skills
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving popular skills: {str(e)}"
        )