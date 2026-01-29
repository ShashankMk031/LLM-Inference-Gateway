# Global API Key middleware 
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
import hashlib
from cachetools import TTLCache
import asyncio
from ..db.session import get_session
from ..db.base import APIKey

# In-memory cache for validated API keys (hash -> key_id)
# TTL of 1 hour, max 1000 keys
api_key_cache = TTLCache(maxsize=1000, ttl=3600)
cache_lock = asyncio.Lock()

class APIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        # Skip health/root/frontend and auth endpoints
        # Also skip analytics (uses JWT)
        if (request.url.path in ["/", "/health", "/login", "/api-keys", "/docs", "/openapi.json"] 
            or request.url.path.startswith("/analytics")
            or request.url.path.startswith("/frontend")):
            return await call_next(request)
        
        api_key_header = request.headers.get("X-API-KEY") or request.headers.get("Authorization")
        if not api_key_header:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API Key required")

        # Strip "Bearer" prefix if present
        if api_key_header.startswith("Bearer "):
            api_key_header = api_key_header[len("Bearer "):]
        
        # Use hash of API key as cache key (avoid storing plaintext in cache)
        cache_key = hashlib.sha256(api_key_header.encode()).hexdigest()
        
        validated_key = None
        
        # Check cache first (thread-safe access)
        async with cache_lock:
            cached_key_id = api_key_cache.get(cache_key)
        
        if cached_key_id:
            # Cache hit - fetch by ID (fast indexed lookup)
            async with get_session() as db:
                result = await db.execute(
                    select(APIKey).where(APIKey.id == cached_key_id, APIKey.active == True)
                )
                validated_key = result.scalar_one_or_none()
        
        if not validated_key:
            # Cache miss - do expensive bcrypt validation
            async with get_session() as db:
                result = await db.execute(select(APIKey).where(APIKey.active == True))
                db_keys = result.scalars().all()

                for db_key in db_keys:
                    if bcrypt.checkpw(api_key_header.encode(), db_key.key_hash.encode()):
                        validated_key = db_key
                        # Cache the key ID
                        async with cache_lock:
                            api_key_cache[cache_key] = db_key.id
                        break
        
        if not validated_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                content={"detail": "Invalid API Key"}
            )
        
        # Attach to request.state for all endpoints 
        request.state.user_id = validated_key.owner_id
        request.state.api_key = validated_key

        response = await call_next(request) 
        return response