from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

# Dummy in-memory data (MVP)
collaborations = [
    {
        "id": 1,
        "labs": "AI Lab ↔ Computer Vision Lab",
        "status": "Recommended",
        "score": 92
    },
    {
        "id": 2,
        "labs": "Bioinformatics Lab ↔ Genetics Lab",
        "status": "Pending",
        "score": 88
    }
]

emails = []

@router.get("/")
def get_collaborations():
    return collaborations

@router.post("/generate-email")
def generate_email(lab_pair: str):
    email = {
        "to": "collab@university.edu",
        "subject": f"Collaboration Opportunity: {lab_pair}",
        "body": f"""
Hello,

We identified a strong collaboration opportunity between:
{lab_pair}

Please let us know if you are interested.

Regards,
MCP Atlas System
""",
        "timestamp": datetime.utcnow()
    }

    emails.append(email)
    return {"message": "Email generated", "email": email}

@router.get("/emails")
def email_history():
    return emails
