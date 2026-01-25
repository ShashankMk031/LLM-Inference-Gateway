from ..router.model_router import router
from ..providers.registry import get_provider
from ..providers.base import ProviderTemporaryError, ProviderPermanentError

FALLBACK_ORDER = ["openai", "gemini", "groq", "mock"]

async def run_inference(model: str, prompt: str, max_tokens: int) -> ProviderResponse:
    """Run inference with smart routing."""
    
    # Smart model selection
    selected_model = model
    if model == "auto":
        selected_model = router.select_provider(auto=True)
    
    # Primary attempt
    try:
        provider = get_provider(selected_model)
        if not await provider.is_healthy():
            raise ProviderTemporaryError(f"{selected_model} unhealthy")
        
        return await provider.infer(prompt, max_tokens)
    
    # Single fallback on temporary failure
    except ProviderTemporaryError:
        for fallback in FALLBACK_ORDER:
            if fallback != selected_model:
                try:
                    provider = get_provider(fallback)
                    return await provider.infer(prompt, max_tokens)
                except ProviderPermanentError:
                    continue
        raise ProviderPermanentError("All fallbacks exhausted")
    
    except ProviderPermanentError:
        raise  # Don't fallback permanent errors
