import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "your-secret-key-here"  # Default, should be overridden by env var
    REDIS_URL: str = "redis://localhost:6379/0" # Default Redis URL

    class Config:
        env_file = ".env"

settings = Settings()

# Handle asyncpg driver (keep existing logic but use settings)
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

if "postgresql://" in DATABASE_URL and "postgresql+asyncpg://" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DATABASE_URL, 
    echo=True, # Logs SQL 
    pool_pre_ping=True, # Checks connection before using it 
    pool_recycle=3600 # Recycle connections every hour
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)