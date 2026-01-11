# Sliding window 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from redis.asyncio import Redis
from ..config import settings
import functools
import hashlib
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

# Custom per-key limit (Overrides default) 
def get_key_limit(key_id: str) -> str:
    """Compute deterministic rate limit from key_id via sha256 hash, returning 'N per minute'"""
    # Safe deterministic hash to integer
    hash_val = int(hashlib.sha256(key_id.encode()).hexdigest(), 16)
    offset = hash_val % 50
    return f"{50 + offset} per minute" 

# Cache for decorated functions to avoid recreation (Bounded LRU)
_limiter_cache = LRUCache(maxsize=100)

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
            
            if cache_key not in _limiter_cache:
                # Create and cache the decorated function 
                # Note: limiter.limit returns a decorator, which we apply to the function
                limit_decorator = limiter.limit(limit_str)
                # We need to wrap the original function, but preserve async behavior
                # limiter.limit wraps the function to add limit check
                
                @limit_decorator
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
