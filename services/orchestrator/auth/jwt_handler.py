"""
JWT token handling for authentication
"""
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from config import settings
from typing import Optional, Dict, Any
import uuid

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    # Truncate password to 72 bytes for bcrypt
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Truncate password to 72 bytes for bcrypt
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.access_token_expire_days)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def get_current_user(token = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    if not token.credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    
    try:
        payload = decode_token(token.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_user_token(user_id: str, email: str, name: str, role: str = "member") -> str:
    """Create token for a user"""
    token_data = {
        "sub": user_id,
        "email": email,
        "name": name,
        "role": role
    }
    return create_access_token(token_data)


def generate_user_id() -> str:
    """Generate unique user ID"""
    return str(uuid.uuid4())
