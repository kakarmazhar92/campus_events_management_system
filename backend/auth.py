# backend/auth.py
import os, hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
import models

SECRET_KEY  = os.getenv("SECRET_KEY", "campus_secret_change_in_production_2024")
ALGORITHM   = "HS256"
ACCESS_TTL  = 60 * 24 * 7   # 7 days in minutes

bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = "campus_user_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

def create_token(user_id: int, email: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TTL)
    return jwt.encode({"sub": str(user_id), "email": email, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return db.query(models.User).filter(models.User.id == user_id).first()
    except Exception:
        return None