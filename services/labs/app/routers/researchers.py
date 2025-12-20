from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas, crud

router = APIRouter(prefix="/researchers", tags=["Researchers"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[schemas.ResearcherResponse])
def get_researchers(db: Session = Depends(get_db)):
    return db.query(models.Researcher).all()

@router.post("/", response_model=schemas.ResearcherResponse)
def create_researcher(researcher: schemas.ResearcherCreate, db: Session = Depends(get_db)):
    """Create a researcher - starts in pending status"""
    try:
        return crud.create_researcher(db, researcher)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/by-lab/{lab_id}")
def get_researchers_by_lab(lab_id: int, db: Session = Depends(get_db)):
    return db.query(models.Researcher).filter(models.Researcher.lab_id == lab_id).all()

@router.post("/{researcher_id}/accept")
def accept_invitation(researcher_id: int, orchestrator_user_id: str, db: Session = Depends(get_db)):
    """Accept researcher invitation"""
    try:
        return crud.accept_researcher_invitation(db, researcher_id, orchestrator_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{researcher_id}/reject")
def reject_invitation(researcher_id: int, db: Session = Depends(get_db)):
    """Reject researcher invitation"""
    try:
        return crud.reject_researcher_invitation(db, researcher_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
