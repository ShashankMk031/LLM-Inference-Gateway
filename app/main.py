import logging
from fastapi import FastAPI, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .db.session import get_db
from .db.base import Base
from .config import engine
from .auth.jwt import get_password_hash, create_access_token, Token, get_current_user
from .auth.apikey import create_api_key, verify_api_key
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Inference Gateway")

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


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown (if needed)
    # await engine.dispose()


app = FastAPI(title="LLM Inference Gateway", lifespan=lifespan)

# Test endpoint of authentication
class LoginForm(BaseModel):
    email: str
    password: str 

@app.post("/login", response_model=Token)
async def login(form: LoginForm, db: AsyncSession = Depends(get_db)):
    # Dummy user lookup + verify ( replace with real User model query) 
    # user = await get_user_by_email( form.email)
    # if not verify_password(form.password, user.hashed_password):
    #    raise HTTPException(401, "Invalid credentials")
    return Token(access_token=create_access_token({"sub": form.email}), token_type="Bearer") 

@app.post("/api-keys")
async def generate_key(db: AsyncSession = Depends(get_db)):
    key = await create_api_key(db)
    return {"api_key": key, "message": "Save this securely - shown once"}

@app.get("/protected-jwt")
async def protected_jwt(current_user = Depends(get_current_user)):
    return {"user": current_user}

@app.get("/protected-apikey")
async def protected_apikey(api_key = Depends(verify_api_key)):
    return {"message": "API key auth works!", "key_id": api_key.id}