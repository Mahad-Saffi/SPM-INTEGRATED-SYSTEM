"""
FastAPI Dependencies - JWT Validation and Authentication
"""
import os
import jwt
from fastapi import Header, HTTPException, status
from typing import Optional, Dict, Any

# Atlas JWT Configuration
ATLAS_JWT_SECRET = os.getenv("ATLAS_JWT_SECRET", "your-secret-key-change-in-production")
ATLAS_API_URL = os.getenv("ATLAS_API_URL", "http://localhost:8000")
# Allow bypassing auth for local development
ALLOW_LOCAL_AUTH_BYPASS = os.getenv("ALLOW_LOCAL_AUTH_BYPASS", "true").lower() == "true"

async def verify_atlas_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Verify Atlas JWT token from Authorization header
    Returns decoded token payload with user_id, email, role
    For local development, allows bypassing authentication
    """
    # Allow bypassing auth for local development
    if ALLOW_LOCAL_AUTH_BYPASS and not authorization:
        return {
            "user_id": "local_user",
            "id": "local_user",
            "email": "local@localhost",
            "role": "owner"
        }
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        # For local development, if no Bearer token, return default user
        if ALLOW_LOCAL_AUTH_BYPASS:
            return {
                "user_id": "local_user",
                "id": "local_user",
                "email": "local@localhost",
                "role": "owner"
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )
    
    token = authorization.replace("Bearer ", "").strip()
    
    # For local development, if token is "local" or empty, bypass
    if ALLOW_LOCAL_AUTH_BYPASS and (token == "local" or not token):
        return {
            "user_id": "local_user",
            "id": "local_user",
            "email": "local@localhost",
            "role": "owner"
        }
    
    try:
        payload = jwt.decode(token, ATLAS_JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        if ALLOW_LOCAL_AUTH_BYPASS:
            return {
                "user_id": "local_user",
                "id": "local_user",
                "email": "local@localhost",
                "role": "owner"
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        if ALLOW_LOCAL_AUTH_BYPASS:
            return {
                "user_id": "local_user",
                "id": "local_user",
                "email": "local@localhost",
                "role": "owner"
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

def require_manager(current_user: Dict[str, Any]) -> None:
    """Require manager or owner role"""
    role = current_user.get("role", "").lower()
    if role not in ["manager", "owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )

def require_owner(current_user: Dict[str, Any]) -> None:
    """Require owner role"""
    role = current_user.get("role", "").lower()
    if role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )


