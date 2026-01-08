import secrets
import bcrypt
import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import APIKey
from ..db.session import get_db
from fastapi import HTTPException, status, Header, Depends


async def create_api_key(db: AsyncSession) -> str:
    # generate secure random API keys, hash it, store active entry
    raw_key = secrets.token_urlsafe(32)  # 43 chars, cryptographically secure
    loop = asyncio.get_running_loop()

    def _compute_hash(key: str) -> str:
        return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()

    key_hash = await loop.run_in_executor(None, _compute_hash, raw_key)

    api_key = APIKey(key_hash=key_hash, rate_limit=100, active=True)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return raw_key  # Return raw (client keeps it), hash stored in DB


async def verify_api_key(api_key: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    # Verify raw API key against hashed DB entries
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key required")

    key_bytes = api_key.encode()
    result = await db.execute(select(APIKey).where(APIKey.active == True))
    db_keys = result.scalars().all()

    if not db_keys:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    loop = asyncio.get_running_loop()
    max_concurrency = 50
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _check_db_key(db_key: APIKey) -> bool:
        async with semaphore:
            return await loop.run_in_executor(None, bcrypt.checkpw, key_bytes, db_key.key_hash.encode())

    tasks = [asyncio.create_task(_check_db_key(db_key)) for db_key in db_keys]
    task_map = {t: k for t, k in zip(tasks, db_keys)}

    try:
        for fut in asyncio.as_completed(tasks):
            try:
                match = await fut
            except asyncio.CancelledError:
                continue
            if match:
                # cancel remaining tasks
                for t in tasks:
                    if not t.done():
                        t.cancel()
                return task_map[fut]  # Valid key found
    finally:
        # ensure all tasks are cleaned up
        await asyncio.gather(*tasks, return_exceptions=True)

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")