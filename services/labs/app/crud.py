from sqlalchemy.orm import Session
from . import models, schemas, auth

# Users
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# Labs
def get_labs(db: Session):
    return db.query(models.Lab).all()

def get_lab(db: Session, lab_id: int):
    return db.query(models.Lab).filter(models.Lab.id == lab_id).first()

def create_lab(db: Session, lab: schemas.LabBase):
    db_lab = models.Lab(**lab.dict())
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab
