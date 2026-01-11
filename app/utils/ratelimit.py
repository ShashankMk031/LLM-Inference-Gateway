# Sliding window 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from redis.asyncio import Redis
from ..config import settings
import time

# Reddis connection (reuse across the app)
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses = True)

limiter = Limiter(
    key_func= lambda request: f"{request.state.api_key.id}:{get_remote_address(request)}",
    default_limits = ["100 per minute"], # Fallback rate limit
    storage_uri = settings.REDIS_URL,
    enabled= True
)

# Custom per-key limit (Overrides default) 
async def get_key_limit(key_id: str) -> str:
    # Fetch rate limit from APIKey model, format as "X per minute"
    # query DB for key_id.rate_limit
    # For demo: fixed per key 
    return f"{50+ int(key_id) % 50} per minute" # Example logic

# Rate limit decorator using key-specific limit
def api_key_limiter(window: str = "1 minute"):
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            key_id = request.state.api_key.id
            limit_str= await get_key_limit(str(key_id))

            @limiter.limit(limit_str)
            async def limited():
                return await func(request, *args, **kwargs)
            
            return await limited()
        return wrapper
    return decorator

#Global middleware
middleware = SlowAPIMiddleware

# 429 Handler
def rate_limit_handler(request, exc):
    return _rate_limit_exceeded_handler(request, exc)