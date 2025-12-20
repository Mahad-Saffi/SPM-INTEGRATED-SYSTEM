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

def get_labs_for_user(db: Session, user_id: str):
    """Get labs created by or accessible to a user"""
    return db.query(models.Lab).filter(
        models.Lab.orchestrator_user_id == user_id
    ).all()

def get_lab(db: Session, lab_id: int):
    return db.query(models.Lab).filter(models.Lab.id == lab_id).first()

def create_lab(db: Session, lab: schemas.LabCreate, user_id = None):
    """Create a lab with optional user_id and set creator as head"""
    lab_dict = lab.dict()
    
    # If user_id is provided as parameter, use it; otherwise use from lab object
    if user_id:
        lab_dict['orchestrator_user_id'] = user_id
    
    orchestrator_user_id = lab_dict.get('orchestrator_user_id')
    
    # Find or create the user in Labs database
    head_user = None
    if orchestrator_user_id:
        head_user = db.query(models.User).filter(
            models.User.orchestrator_user_id == orchestrator_user_id
        ).first()
        
        # If user doesn't exist in Labs DB, create a placeholder
        if not head_user:
            head_user = models.User(
                orchestrator_user_id=orchestrator_user_id,
                name="Lab Head",
                email=f"user-{orchestrator_user_id}@labs.local",
                hashed_password="",
                is_active=True
            )
            db.add(head_user)
            db.flush()  # Get the ID without committing
    
    # Set the head_id to the creator
    if head_user:
        lab_dict['head_id'] = head_user.id
    
    db_lab = models.Lab(**lab_dict)
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab


def create_researcher(db: Session, researcher: schemas.ResearcherCreate):
    """Create a researcher - starts in pending status until they accept"""
    researcher_dict = researcher.dict()
    
    # Check if email already exists
    existing_researcher = db.query(models.Researcher).filter(
        models.Researcher.email == researcher_dict['email']
    ).first()
    
    if existing_researcher:
        raise ValueError(f"Researcher with email {researcher_dict['email']} already exists")
    
    # Create researcher in pending status
    researcher_dict['status'] = 'pending'
    
    db_researcher = models.Researcher(**researcher_dict)
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    
    # TODO: Send email to researcher with invitation link
    # The email should contain a link to accept/reject the role
    
    return db_researcher


def accept_researcher_invitation(db: Session, researcher_id: int, orchestrator_user_id: str):
    """Accept researcher invitation and activate the researcher"""
    researcher = db.query(models.Researcher).filter(
        models.Researcher.id == researcher_id
    ).first()
    
    if not researcher:
        raise ValueError(f"Researcher with id {researcher_id} not found")
    
    if researcher.status != 'pending':
        raise ValueError(f"Researcher is not in pending status")
    
    # Update researcher status and link to orchestrator user
    researcher.status = 'active'
    researcher.orchestrator_user_id = orchestrator_user_id
    db.commit()
    db.refresh(researcher)
    
    return researcher


def reject_researcher_invitation(db: Session, researcher_id: int):
    """Reject researcher invitation"""
    researcher = db.query(models.Researcher).filter(
        models.Researcher.id == researcher_id
    ).first()
    
    if not researcher:
        raise ValueError(f"Researcher with id {researcher_id} not found")
    
    if researcher.status != 'pending':
        raise ValueError(f"Researcher is not in pending status")
    
    # Update researcher status to rejected
    researcher.status = 'rejected'
    db.commit()
    db.refresh(researcher)
    
    return researcher
