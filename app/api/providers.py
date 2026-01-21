from fastapi import APIRouter
from ..providers.registry import list_providers
import asyncio

router = APIRouter(prefix="/providers", tags=["providers"])

@router.get("/")
async def get_providers():
    # List all available providers with health status
    providers_list = list_providers()
    # Collect health check coroutines
    health_tasks = [(name, provider.is_healthy()) for name, provider in providers_list]
    # Run all health checks concurrently
    results = await asyncio.gather(*[coro for _, coro in health_tasks], return_exceptions=True)
    # Map results back to provider names
    providers = []
    for (name, _), result in zip(health_tasks, results):
        healthy = result is True
        providers.append({
            "name": name,
            "healthy": healthy
        })
    return providers