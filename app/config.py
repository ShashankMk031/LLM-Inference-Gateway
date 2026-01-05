import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL")

# Changing to postgresSQL+asyncpg for async 
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")

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