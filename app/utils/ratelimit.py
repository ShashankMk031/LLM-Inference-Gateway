# Sliding window 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from redis.asyncio import Redis
from ..config import settings

# Reddis connection (reuse across the app)
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses = True)

limiter = Limiter(
    key_func=lambda request: (
        f"{request.state.api_key.id}:{get_remote_address(request)}"
        if hasattr(request.state, "api_key") and request.state.api_key
        else get_remote_address(request)
    ),
    default_limits = ["100 per minute"], # Fallback rate limit
    storage_uri = settings.REDIS_URL,
    enabled=True
)

import functools
import hashlib

# Custom per-key limit (Overrides default) 
async def get_key_limit(key_id: str) -> str:
    # Fetch rate limit from APIKey model, format as "X per minute"
    # Safe deterministic hash to integer
    hash_val = int(hashlib.sha256(key_id.encode()).hexdigest(), 16)
    offset = hash_val % 50
    return f"{50 + offset} per minute" 

# Cache for decorated functions to avoid recreation
_limiter_cache = {}

# Rate limit decorator using key-specific limit
def api_key_limiter(window: str = "1 minute"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request, *args, **kwargs):
            key_id = request.state.api_key.id
            limit_str = await get_key_limit(str(key_id))
            
            # Cache key: (function reference, limit string)
            cache_key = (func, limit_str)
            
            if cache_key not in _limiter_cache:
                # Create and cache the decorated function
                @limiter.limit(limit_str)
                @functools.wraps(func)
                async def limited(request, *args, **kwargs):
                    return await func(request, *args, **kwargs)
                _limiter_cache[cache_key] = limited
            
            return await _limiter_cache[cache_key](request, *args, **kwargs)
        return wrapper
    return decorator

#Global middleware
middleware = SlowAPIMiddleware

# 429 Handler
def rate_limit_handler(request, exc):
    return _rate_limit_exceeded_handler(request, exc)