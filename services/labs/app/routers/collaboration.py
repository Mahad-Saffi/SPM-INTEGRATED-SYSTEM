from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from .. import models, schemas, database, crud
from typing import List

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_collaboration_score(lab1: models.Lab, lab2: models.Lab) -> int:
    """
    Calculate collaboration score between two labs based on:
    - Research focus similarity
    - Researcher expertise overlap
    - Geographic proximity (if available)
    """
    score = 0
    
    # Check research focus similarity
    if lab1.domain and lab2.domain:
        if lab1.domain.lower() == lab2.domain.lower():
            score += 40
        elif any(word in lab2.domain.lower() for word in lab1.domain.lower().split()):
            score += 20
    
    # Check researcher expertise overlap
    researchers1 = set()
    researchers2 = set()
    
    if hasattr(lab1, 'researchers'):
        researchers1 = {r.field.lower() for r in lab1.researchers if r.field}
    if hasattr(lab2, 'researchers'):
        researchers2 = {r.field.lower() for r in lab2.researchers if r.field}
    
    overlap = researchers1.intersection(researchers2)
    score += len(overlap) * 15
    
    # Cap at 100
    return min(score + 30, 100)  # Base score of 30 + calculated

@router.get("/suggestions")
def get_collaboration_suggestions(db: Session = Depends(get_db)) -> List[dict]:
    """
    Get suggested collaborations between labs
    Based on research focus and researcher expertise
    """
    labs = db.query(models.Lab).all()
    suggestions = []
    
    # Compare each pair of labs
    for i, lab1 in enumerate(labs):
        for lab2 in labs[i+1:]:
            score = calculate_collaboration_score(lab1, lab2)
            
            # Only suggest if score is above 60
            if score >= 60:
                suggestions.append({
                    "id": f"{lab1.id}_{lab2.id}",
                    "lab1_id": lab1.id,
                    "lab1_name": lab1.name,
                    "lab2_id": lab2.id,
                    "lab2_name": lab2.name,
                    "labs": f"{lab1.name} ↔ {lab2.name}",
                    "status": "Recommended",
                    "score": score,
                    "reason": f"Similar research focus: {lab1.domain} and {lab2.domain}"
                })
    
    # Sort by score
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions

@router.post("/accept/{lab1_id}/{lab2_id}")
def accept_collaboration(
    lab1_id: int,
    lab2_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Accept a collaboration suggestion
    Creates formal collaboration record
    """
    lab1 = db.query(models.Lab).filter(models.Lab.id == lab1_id).first()
    lab2 = db.query(models.Lab).filter(models.Lab.id == lab2_id).first()
    
    if not lab1 or not lab2:
        return {"error": "Lab not found"}
    
    # Create collaboration record
    collaboration = models.Collaboration(
        lab_id=lab1_id,
        researcher_id=None,  # Can be extended to track specific researchers
        title=f"Collaboration: {lab1.name} ↔ {lab2.name}",
        description=f"Formal collaboration between {lab1.name} and {lab2.name}"
    )
    
    db.add(collaboration)
    db.commit()
    db.refresh(collaboration)
    
    return {
        "message": "Collaboration accepted",
        "collaboration": {
            "id": collaboration.id,
            "lab1": lab1.name,
            "lab2": lab2.name,
            "status": "Active",
            "created_at": collaboration.created_at
        }
    }

@router.post("/generate-email")
def generate_collaboration_email(lab_pair: str) -> dict:
    """
    Generate collaboration email between two labs
    """
    email = {
        "to": "collab@university.edu",
        "subject": f"Collaboration Opportunity: {lab_pair}",
        "body": f"""
Hello,

We identified a strong collaboration opportunity between:
{lab_pair}

This collaboration could lead to:
- Shared research resources
- Joint publications
- Cross-training of researchers
- Combined grant opportunities

Please let us know if you are interested.

Regards,
Research Collaboration System
""",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return {"message": "Email generated", "email": email}

@router.get("/emails")
def get_email_history(db: Session = Depends(get_db)) -> List[dict]:
    """Get history of generated collaboration emails"""
    # In a real system, this would query a database
    # For now, returning empty list
    return []

@router.get("/active")
def get_active_collaborations(db: Session = Depends(get_db)) -> List[dict]:
    """Get all active collaborations"""
    collaborations = db.query(models.Collaboration).all()
    return [
        {
            "id": c.id,
            "lab_id": c.lab_id,
            "lab_name": c.lab.name if c.lab else "Unknown",
            "title": c.title,
            "description": c.description,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in collaborations
    ]

