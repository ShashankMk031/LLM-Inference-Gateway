# Sliding window 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from redis.asyncio import Redis
from ..config import settings
import functools
import hashlib
import asyncio
from cachetools import LRUCache

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

# In-memory config sources (Simulating DB/Config Store)
KEY_LIMITS = {
    "1": "50 per minute",  # Admin Key
    "2": "20 per minute",  # User Key
}
DEFAULT_TIER_LIMIT = "10 per minute"

# Custom per-key limit (Overrides default) 
def get_key_limit(key_id: str) -> str:
    """
    Fetch explicit configured limit for the API key.
    Falls back to a tier-based default if not found.
    """
    return KEY_LIMITS.get(str(key_id), DEFAULT_TIER_LIMIT)

# Cache for decorated functions to avoid recreation (Bounded LRU)
_limiter_cache = LRUCache(maxsize=100)
_cache_lock = asyncio.Lock()

# Rate limit decorator using key-specific limit
def api_key_limiter():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Verify api_key exists
            if not hasattr(request.state, "api_key") or not request.state.api_key:
                raise ValueError("api_key_limiter requires request.state.api_key to be set")
            
            key_id = request.state.api_key.id
            limit_str = get_key_limit(str(key_id))
            
            # Cache key: (function reference, limit string)
            cache_key = (func, limit_str)
            
            # Double-checked locking optimization
            async with _cache_lock:
                if cache_key not in _limiter_cache:
                    limit_decorator = limiter.limit(limit_str)
                    
                    @limit_decorator
                    @functools.wraps(func)
                    async def limited(request, *args, **kwargs):
                        return await func(request, *args, **kwargs)
                    
                    _limiter_cache[cache_key] = limited
                
                cached_func = _limiter_cache[cache_key]
            
            return await cached_func(request, *args, **kwargs)
        return wrapper
    return decorator

#Global middleware
middleware = SlowAPIMiddleware

# 429 Handler
def rate_limit_handler(request, exc):
    return _rate_limit_exceeded_handler(request, exc)
