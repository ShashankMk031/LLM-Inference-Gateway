import secrets 
import bcrypt 
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import APIKey
from fastapi import HTTPException, status, Header, Depends 

async def create_api_key(db: AsyncSession) -> str: 
    # generate secure random API keys, hash it, store active entry 
    raw_key = secrets.token_urlsafe(32) # 43 chars, cryptographically secure
    loop = asyncio.get_running_loop()

    def _compute_hash(key: str) -> str:
        return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()

    key_hash = await loop.run_in_executor(None, _compute_hash, raw_key)

    api_key = APIKey(key_hash = key_hash, rate_limit = 100, active = True) 
    db.add(api_key) 
    await db.commit() 
    await db.refresh(api_key)
    return raw_key # Return raw (client keeps it), hash stored in DB

async def verify_api_key(api_key: str = Header(None), db : AsyncSession = Depends(get_db)):
    # Verify raw API key against hashed DB entries 
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key required") 
    
    key_bytes = api_key.encode() 
    result = await db.execute(select(APIKey).where(APIKey.active == True)) 
    db_keys = result.scalars().all() 

    for db_key in db_keys:
        if bcrypt.checkpw(key_bytes, db_key.key_hash.encode()):
            return db_key  # Valid key found 
    
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")