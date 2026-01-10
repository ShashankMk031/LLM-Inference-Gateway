# Global API Key middleware 
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from ..db.session import get_session
from ..db.base import APIKey

class APIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        # Skip health/root and auth endpoints
        if request.url.path in ["/", "/health", "/login", "/api-keys", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        api_key_header = request.headers.get("X-API-KEY") or request.headers.get("Authorization")
        if not api_key_header:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API Key required")

        # Stripe "Bearer" prefix if present
        if api_key_header.startswith("Bearer "):
            api_key_header = api_key_header[len("Bearer "):]
        


        validated_key = None
        # Verify against DB 
        async with get_session() as db:
            result = await db.execute(select(APIKey).where(APIKey.active == True))
            db_keys = result.scalars().all()

            for db_key in db_keys:
                if bcrypt.checkpw(api_key_header.encode(), db_key.key_hash.encode()):
                    validated_key = db_key
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