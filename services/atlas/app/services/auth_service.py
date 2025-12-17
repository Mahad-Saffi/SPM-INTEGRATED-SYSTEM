from datetime import datetime, timedelta
import jwt
from starlette.config import Config
import bcrypt

config = Config(".env")

class AuthService:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        try:
            # Ensure password is bytes
            if isinstance(plain_password, str):
                plain_password = plain_password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(plain_password, hashed_password)
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        try:
            # Ensure password is bytes and truncate to 72 bytes if needed
            if isinstance(password, str):
                password = password.encode('utf-8')
            
            # Bcrypt has a 72 byte limit
            if len(password) > 72:
                password = password[:72]
            
            # Generate salt and hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password, salt)
            
            # Return as string
            return hashed.decode('utf-8')
        except Exception as e:
            print(f"Password hashing error: {e}")
            raise

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config('JWT_SECRET_KEY'), algorithm="HS256")
        return encoded_jwt

auth_service = AuthService()
