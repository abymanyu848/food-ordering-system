from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.settings import settings
from app.models.user import User, UserRole
from app.database import get_db

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password[:72])


def verify_password(plain_password: str, stored_password: str) -> bool:
    if not stored_password:
        return False
    # Legacy seed/test accounts were stored as plain text; support them and
    # allow callers to re-hash on successful login.
    if not stored_password.startswith(("$2a$", "$2b$", "$2y$")):
        return plain_password == stored_password
    try:
        return pwd_context.verify(plain_password[:72], stored_password)
    except Exception:
        return False


def needs_rehash(stored_password: str) -> bool:
    if not stored_password.startswith(("$2a$", "$2b$", "$2y$")):
        return True
    try:
        return pwd_context.needs_update(stored_password)
    except Exception:
        return False

# JWT token handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_current_active_restaurant(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.RESTAURANT:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_current_active_delivery_person(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.DELIVERY_PERSON:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_current_restaurant_or_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role not in [UserRole.RESTAURANT, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user