from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import models, schemas, database, crud

router = APIRouter(prefix="/labs", tags=["Labs"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[schemas.LabResponse])
def read_labs(user_id: str = Query(None), db: Session = Depends(get_db)):
    """Get labs - if user_id provided, only return labs created by that user"""
    if user_id:
        return crud.get_labs_for_user(db, user_id)
    return crud.get_labs(db)

@router.get("/{lab_id}", response_model=schemas.LabResponse)
def read_lab(lab_id: int, db: Session = Depends(get_db)):
    lab = crud.get_lab(db, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return lab

@router.post("/", response_model=schemas.LabResponse)
def create_lab(lab: schemas.LabCreate, db: Session = Depends(get_db)):
    """Create a new lab - orchestrator_user_id should be in the request body"""
    return crud.create_lab(db, lab, lab.orchestrator_user_id)
