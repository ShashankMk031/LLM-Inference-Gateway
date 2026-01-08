import secrets 
import bcrypt 
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import APIKey
from fastapi import HTTPException, status, Header, Depends 

async def create_api_key(db: AsyncSession) -> str: 
    # generate secure random API keys, hash it, store active entry 
    raw_key = secrets.token_urlsafe(32) # 43 chars, cryptographically secure
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode() 

    api_key = APIKey(key_hash = key_hash, rate_limit = 100, active = True) 
    db.add(api_key) 
    await db.commit() 
    await db.refresh(api_key)
    return raw_key # Return raw (client keeps it), hash stored in DB

