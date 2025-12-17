from fastapi import APIRouter, Depends, HTTPException
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
def read_labs(db: Session = Depends(get_db)):
    return crud.get_labs(db)

@router.post("/", response_model=schemas.LabResponse)
def create_lab(lab: schemas.LabBase, db: Session = Depends(get_db)):
    return crud.create_lab(db, lab)
