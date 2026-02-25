import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt

# In production, these should be loaded from environment variables (.env)
SECRET_KEY = os.getenv("KRYSTAL_SECRET_KEY", "b3a4f6d891e024b7a1cd89b0f1a23c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
