from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import AsyncSessionLocal # From parent config 

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]: 
    async with AsyncSessionLocal() as session: 
        yield session 
        await session.commit() # Auto-commit after use per request 

async def get_db() -> AsyncGenerator[AsyncSession, None]: 
    async with get_session() as session: 
        yield session