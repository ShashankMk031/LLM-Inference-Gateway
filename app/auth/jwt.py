import jwt 
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from ..config import settings 

SECRET_KEY= settings.SECRET_KEY 
ALGORITHM = "HS256" 
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

security = HTTPBearer() 

class Token(BaseModel):
    access_token: str 
    token_type: str 

def verify_password(plain: str, hashed: str) -> bool: 
    return pwd_context.verify(plain, hashed) 

def get_password_hash(password: str) -> str: 
    return pwd_context.hash(password) 

def create_access_token(data: dict) -> str: 
    to_encode = data.copy() 
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES) 
    to_encode.update({"exp": expire}) 
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) 
    return encoded 

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Invalid credentials",
        headers = {"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") 
        if email is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    # fetch user from DB by email (dummy for now)
    return {"email": email}