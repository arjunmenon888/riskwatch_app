import os
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Import local modules to avoid circular import issues
import models
import database

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# It's crucial that these are loaded from your environment and not hardcoded
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token valid for 24 hours

# --- Password Hashing Setup ---
# We use bcrypt as the hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain text password."""
    return pwd_context.hash(password)

# --- JWT Token Handling ---
def create_access_token(data: dict) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- FastAPI Dependencies for Authentication ---

# This tells FastAPI where the client will send the username and password to get a token
# It's used internally by the `Depends(oauth2_scheme)` dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
) -> models.User:
    """
    Dependency to get the current user from a JWT token.
    This is used for standard HTTP API routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = get_user_from_token(token, db)
    if user is None:
        raise credentials_exception
    
    return user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency to ensure the current user is an admin.
    Builds on top of `get_current_user`.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required"
        )
    return current_user

# --- Helper Function for WebSocket Authentication ---

def get_user_from_token(token: str, db: Session) -> models.User | None:
    """
    Decodes a JWT token and returns the corresponding user from the database.
    This is a standalone function used by the WebSocket endpoint, as it cannot
    use the standard FastAPI `Depends` system.
    Returns the User object on success, or None on failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_id = uuid.UUID(user_id_str) # Convert string back to UUID object
        
    except (JWTError, ValueError):
        # Catches decoding errors or if user_id is not a valid UUID
        return None
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    return user