from fastapi import APIRouter
from ..providers.registry import list_providers

router = APIRouter(prefix="/providers", tags=["providers"])

@router.get("/")
async def get_providers():
    # List all available providers with health status
    providers = []
    for name , provider in list_providers():
        providers.append({
            "name":name,
            "healthy": await provider.is_healthy()
        })
    return providers