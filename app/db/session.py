from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import AsyncSessionLocal # From parent config 

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]: 
    async with AsyncSessionLocal() as session: 
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit() 

async def get_db() -> AsyncGenerator[AsyncSession, None]: 
    async with get_session() as session: 
        yield session