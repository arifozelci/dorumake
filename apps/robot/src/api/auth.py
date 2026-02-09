"""
JWT Authentication module for KolayRobot API
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import settings

# JWT Settings - Generate random secret if not configured
SECRET_KEY = settings.jwt_secret_key
if SECRET_KEY == "CHANGE-ME-IN-PRODUCTION-USE-RANDOM-64-CHAR-SECRET":
    # Development fallback - in production this MUST be set via environment variable
    import warnings
    warnings.warn("JWT_SECRET_KEY not set! Using development fallback. Set JWT_SECRET_KEY in production!", UserWarning)
    SECRET_KEY = secrets.token_hex(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours (reduced from 24 for security)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


# Password hashing using PBKDF2-SHA256 (more secure than simple SHA256)
# Use random per-password salt stored with hash
PASSWORD_SALT_LENGTH = 16
PASSWORD_ITERATIONS = 100000  # OWASP recommended minimum

def hash_password(password: str, salt: bytes = None) -> str:
    """
    Hash password with PBKDF2-SHA256 and random salt
    Returns: salt:hash (both hex encoded)
    """
    if salt is None:
        salt = secrets.token_bytes(PASSWORD_SALT_LENGTH)

    # Use PBKDF2 with SHA256
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        PASSWORD_ITERATIONS
    )
    return f"{salt.hex()}:{dk.hex()}"


def verify_password_hash(password: str, stored_hash: str) -> bool:
    """Verify password against stored PBKDF2 hash"""
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_hash = hash_password(password, salt)
        return secrets.compare_digest(expected_hash, stored_hash)
    except (ValueError, AttributeError):
        return False


# Admin password - generate secure hash at startup
# Default admin password: read from ADMIN_PASSWORD env var or generate random
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not DEFAULT_ADMIN_PASSWORD:
    # Generate random password if not set
    DEFAULT_ADMIN_PASSWORD = secrets.token_urlsafe(16)
    import logging
    logging.warning("ADMIN_PASSWORD not set, using random password. Set ADMIN_PASSWORD env var in production.")

ADMIN_PASSWORD_HASH = hash_password(DEFAULT_ADMIN_PASSWORD)

# Hardcoded admin user (can be extended to database later)
ADMIN_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": ADMIN_PASSWORD_HASH,
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return verify_password_hash(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage"""
    return hash_password(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from SQL Server database"""
    # Check hardcoded admin users first (fallback)
    if username in ADMIN_USERS:
        user_dict = ADMIN_USERS[username]
        return UserInDB(**user_dict)

    # Check users from SQL Server
    try:
        from src.db.sqlserver import db as sqlserver_db
        user = sqlserver_db.get_user_by_username(username)
        if user:
            return UserInDB(
                username=user["username"],
                hashed_password=user.get("hashed_password", ""),
                disabled=not user.get("is_active", True)
            )
    except Exception as e:
        # Log error but don't fail
        print(f"Warning: Could not fetch user from database: {e}")

    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
