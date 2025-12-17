from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .. import models, schemas, crud, auth
from ..database import get_db
import uuid

router = APIRouter(prefix="/users", tags=["Users"])


class UserSync(BaseModel):
    orchestrator_user_id: str
    email: str
    name: str


@router.post("/sync")
def sync_user(user_data: UserSync, db: Session = Depends(get_db)):
    """Create or update user from orchestrator"""
    
    # Check if user exists
    existing_user = db.query(models.User).filter(
        models.User.orchestrator_user_id == uuid.UUID(user_data.orchestrator_user_id)
    ).first()
    
    if existing_user:
        existing_user.email = user_data.email
        existing_user.name = user_data.name
        db.commit()
        return {"status": "updated", "user_id": existing_user.id}
    
    # Create new user
    new_user = models.User(
        orchestrator_user_id=uuid.UUID(user_data.orchestrator_user_id),
        email=user_data.email,
        name=user_data.name,
        hashed_password=""  # No password needed for synced users
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "created", "user_id": new_user.id}


@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@router.post("/login", response_model=schemas.Token)
def login_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
