from .metrics import InferenceMetrics
from .logging_service import queue_log
import asyncio
from fastapi import BackgroundTasks
from ..providers.registry import get_provider
from ..providers.base import ProviderResponse, ProviderTemporaryError, ProviderPermanentError
from ..router.model_router import router

async def run_inference(model: str, prompt: str, max_tokens: int, 
                       api_key_id: int, background_tasks: BackgroundTasks) -> ProviderResponse:
    start_time = asyncio.get_event_loop().time()
    
    selected_model = model
    if model == "auto":
        selected_model = router.select_provider(auto=True)
    
    provider_used = selected_model
    
    try:
        provider = get_provider(selected_model)
        result = await provider.infer(prompt, max_tokens)
        
        # Compute latency
        duration = asyncio.get_event_loop().time() - start_time
        
        # Metrics (success)
        metrics = InferenceMetrics.success(
            api_key_id, selected_model, provider.name, result
        )
        metrics.latency_ms = duration * 1000  # Convert to milliseconds
        queue_log(metrics, background_tasks)
        
        return result
        
    except ProviderTemporaryError as e:
        # Compute latency
        duration = asyncio.get_event_loop().time() - start_time
        
        # Log failure and re-raise for proper error handling
        metrics = InferenceMetrics.failure(api_key_id, selected_model, provider_used, "temporary")
        metrics.latency_ms = duration * 1000
        queue_log(metrics, background_tasks)
        raise
        
    except ProviderPermanentError as e:
        # Compute latency
        duration = asyncio.get_event_loop().time() - start_time
        
        metrics = InferenceMetrics.failure(api_key_id, selected_model, provider_used, "permanent")
        metrics.latency_ms = duration * 1000
        queue_log(metrics, background_tasks)
        raise
