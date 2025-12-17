from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import database, models, schemas

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
def create_researcher(researcher: schemas.ResearcherBase, db: Session = Depends(get_db)):
    db_researcher = models.Researcher(**researcher.dict())
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher

@router.get("/by-lab/{lab_id}")
def get_researchers_by_lab(lab_id: int, db: Session = Depends(get_db)):
    return db.query(models.Researcher).filter(models.Researcher.lab_id == lab_id).all()
