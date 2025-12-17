"""
Authentication Manager with Supabase and Local fallback
"""
import hashlib
import os
from datetime import datetime
from typing import Dict, Optional, Any
from components.managers.data_manager import DataManager

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class AuthManager:
    """Handles user authentication with Supabase + Local fallback"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.users = self.load_users()
        self.supabase_client: Optional[Any] = None
        self.use_supabase = False
        
        # Try to initialize Supabase if credentials are available
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if SUPABASE_AVAILABLE and supabase_url and supabase_key:
            try:
                self.supabase_client = create_client(supabase_url, supabase_key)
                self.use_supabase = True
            except Exception as e:
                print(f"Supabase initialization failed, using local fallback: {str(e)}")
        
        self.initialize_default_users()
    
    def load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        users_data = self.data_manager.load_data("users")
        if users_data:
            return users_data
        return {}
    
    def save_users(self) -> bool:
        """Save users to file"""
        return self.data_manager.save_data("users", self.users)
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def initialize_default_users(self):
        """Initialize default users if none exist"""
        if not self.users:
            self.users = {
                "owner@company.com": {
                    "password": self.hash_password("admin123"),
                    "role": "owner",
                    "name": "Project Owner",
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "active": True
                },
                "john@company.com": {
                    "password": self.hash_password("password123"),
                    "role": "employee",
                    "name": "John Doe",
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "active": True
                }
            }
            self.save_users()
    
    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user"""
        # Try Supabase first if available
        if self.use_supabase and self.supabase_client:
            try:
                response = self.supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                if response.user:
                    return {
                        "email": email,
                        "role": response.user.user_metadata.get("role", "employee"),
                        "name": response.user.user_metadata.get("name", email),
                        "authenticated": True
                    }
            except Exception as e:
                print(f"Supabase auth failed: {str(e)}")
        
        # Fallback to local authentication
        hashed_password = self.hash_password(password)
        user = self.users.get(email)
        
        if user and user.get("password") == hashed_password and user.get("active", True):
            return {
                "email": email,
                "role": user.get("role", "employee"),
                "name": user.get("name", email),
                "authenticated": True
            }
        
        return None
    
    def register_user(self, email: str, password: str, name: str, role: str = "employee") -> bool:
        """Register new user"""
        if email in self.users:
            return False
        
        # Try Supabase first if available
        if self.use_supabase and self.supabase_client:
            try:
                response = self.supabase_client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "name": name,
                            "role": role
                        }
                    }
                })
                if response.user:
                    # Also save locally
                    self.users[email] = {
                        "password": self.hash_password(password),
                        "role": role,
                        "name": name,
                        "created_at": datetime.now().strftime("%Y-%m-%d"),
                        "active": True
                    }
                    return self.save_users()
            except Exception as e:
                print(f"Supabase registration failed: {str(e)}")
        
        # Fallback to local registration
        self.users[email] = {
            "password": self.hash_password(password),
            "role": role,
            "name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "active": True
        }
        return self.save_users()
    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        return self.users.get(email)

