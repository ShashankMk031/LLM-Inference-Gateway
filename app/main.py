import logging
import time
from fastapi import FastAPI, Depends, Body, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError, DatabaseError
from contextlib import asynccontextmanager
from .db.session import get_db
from .db.base import Base, User
from .config import engine
from .auth.jwt import create_access_token, Token, get_current_user, verify_password
from .auth.apikey import create_api_key, verify_api_key
from pydantic import BaseModel,ValidationError
from typing import Optional
from .middleware.auth import APIMiddleware

rom .utils.errors import (
    api_error_handler, http_exception_handler, 
    validation_exception_handler, db_integrity_handler, 
    db_connection_handler
)



logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by email from the database."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown (if needed)
    # await engine.dispose()


app = FastAPI(title="LLM Inference Gateway", lifespan=lifespan)



@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        if value == 1:
            return {"status": "healthy", "db": "connected"}
        else:
            return {"status": "unhealthy", "db": "disconnected", "error": "Unexpected query result"}
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return {"status": "unhealthy", "db": "disconnected", "error": str(e)}


# Test endpoint of authentication
class LoginForm(BaseModel):
    email: str
    password: str 


# FIXME(AUTH-001): This login endpoint performs real authentication but should be 
# reviewed before production use to ensure proper security measures are in place.
@app.post("/login", response_model=Token)
async def login(form: LoginForm, db: AsyncSession = Depends(get_db)):
    """Authenticate user and issue JWT token."""
    user = await get_user_by_email(db, form.email)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )
    return Token(access_token=create_access_token({"sub": form.email}), token_type="Bearer") 


@app.post("/api-keys")
async def generate_key(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate a new API key for the authenticated user."""
    # Fetch the user from DB to get their ID
    user = await get_user_by_email(db, current_user["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    key = await create_api_key(db, owner_id=user.id)
    return {"api_key": key, "owner_id": user.id, "message": "Save this securely - shown once"}

from fastapi import Request, Depends

@app.get("/protected")
async def protected_route(request: Request):
    return {
        "message": "Middleware auth works!",
        "api_key_id": request.state.api_key.id,
        "user_id": request.state.user_id
    }

@app.get("/user-info")
async def user_info(request: Request):
    return request.state  # Full context dump

@app.get("/protected-jwt")
async def protected_jwt(current_user = Depends(get_current_user)):
    return {"user": current_user}


@app.get("/protected-apikey")
async def protected_apikey(api_key = Depends(verify_api_key)):
    return {"message": "API key auth works!", "key_id": api_key.id}

# Rate limiting
from .utils.ratelimit import limiter, SlowAPIMiddleware as RateLimitMiddleware, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.add_middleware(RateLimitMiddleware, limiter=limiter)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/hammer")
@limiter.limit("10 per minute")
async def hammer(request: Request):
    return {"hits": time.time(), "key": request.state.api_key.id}

# Add Auth middleware LAST so it runs FIRST (outermost layer)
app.add_middleware(APIMiddleware)

# Exception handlers (order matters—specific first)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, db_integrity_handler)
app.add_exception_handler(DatabaseError, db_connection_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, api_error_handler)  # Catch-all last