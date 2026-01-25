from .metrics import InferenceMetrics
from .logging_service import queue_log

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
        
        # Metrics (success)
        metrics = InferenceMetrics.success(
            api_key_id, selected_model, provider.name, result
        )
        queue_log(metrics, background_tasks)
        
        return result
        
    except ProviderTemporaryError as e:
        # Log failure + fallback
        metrics = InferenceMetrics.failure(api_key_id, selected_model, provider_used, "temporary")
        queue_log(metrics, background_tasks)
        # ... fallback logic ...
        
    except ProviderPermanentError as e:
        metrics = InferenceMetrics.failure(api_key_id, selected_model, provider_used, "permanent")
        queue_log(metrics, background_tasks)
        raise
