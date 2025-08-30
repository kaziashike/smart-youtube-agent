#!/usr/bin/env python3
"""
User Authentication System
Handles user signup, login, and session management
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import jwt

# Configure logging
logger = logging.getLogger(__name__)

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours instead of 30 minutes

# File paths
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "sessions.json")

# Security scheme
security = HTTPBearer()

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    user_id: str
    email: str
    name: str
    company: Optional[str]
    subscription_tier: str
    created_at: str
    youtube_channel: Optional[Dict[str, Any]] = None

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed

def generate_user_id() -> str:
    """Generate unique user ID."""
    return f"user_{secrets.token_hex(8)}"

def load_users() -> Dict[str, Dict[str, Any]]:
    """Load users from JSON file."""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}

def save_users(users: Dict[str, Dict[str, Any]]) -> None:
    """Save users to JSON file."""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        raise HTTPException(status_code=500, detail="Failed to save user data")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.PyJWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    users = load_users()
    user = users.get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def signup_user(user_data: UserSignup) -> Dict[str, Any]:
    """Register a new user."""
    users = load_users()
    
    # Check if email already exists
    for user in users.values():
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = generate_user_id()
    hashed_password = hash_password(user_data.password)
    
    new_user = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": hashed_password,
        "name": user_data.name,
        "company": user_data.company,
        "subscription_tier": "Free",
        "created_at": datetime.utcnow().isoformat(),
        "youtube_channel": None,
        "is_active": True
    }
    
    users[user_id] = new_user
    save_users(users)
    
    # Create user memory file
    create_user_memory(user_id, user_data.name)
    
    # Create free subscription
    from subscription_manager import subscription_manager
    subscription_manager.create_free_subscription(user_id)
    
    logger.info(f"New user registered: {user_data.email}")
    
    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "message": "User registered successfully"
    }

def login_user(login_data: UserLogin) -> Dict[str, Any]:
    """Authenticate user and return access token."""
    users = load_users()
    
    # Find user by email
    user = None
    for u in users.values():
        if u["email"] == login_data.email:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"]}, expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {login_data.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "subscription_tier": user["subscription_tier"]
    }

def create_user_memory(user_id: str, name: str) -> None:
    """Create initial user memory file."""
    try:
        from user_memory import MEMORY_DIR, save_user_memory
        
        if not os.path.exists(MEMORY_DIR):
            os.makedirs(MEMORY_DIR)
        
        initial_memory = {
            "user_id": user_id,
            "name": name,
            "subscription_tier": "Free",
            "created_at": datetime.utcnow().isoformat(),
            "interactions": [],
            "videos": [],
            "auto_mode_enabled": False,
            "youtube_channel": None
        }
        
        save_user_memory(user_id, initial_memory)
        logger.info(f"Created user memory for: {user_id}")
        
    except Exception as e:
        logger.error(f"Error creating user memory for {user_id}: {e}")

def update_user_profile(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile information."""
    users = load_users()
    
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    allowed_fields = ["name", "company", "youtube_channel"]
    for field in allowed_fields:
        if field in updates:
            users[user_id][field] = updates[field]
    
    save_users(users)
    
    # Also update user memory
    try:
        from user_memory import load_user_memory, save_user_memory
        user_memory = load_user_memory(user_id)
        if user_memory:
            for field in allowed_fields:
                if field in updates:
                    user_memory[field] = updates[field]
            save_user_memory(user_id, user_memory)
    except Exception as e:
        logger.error(f"Error updating user memory: {e}")
    
    return users[user_id]

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile by ID."""
    users = load_users()
    return users.get(user_id) 