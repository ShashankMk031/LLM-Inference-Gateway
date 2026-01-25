from fastapi import APIRouter, Request, Depends, HTTPException
from ..api.schemas import InferRequest, InferResponse
from ..services.inference_service import run_inference
from ..providers.base import ProviderTemporaryError, ProviderPermanentError
from ..db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import RequestLog
import logging
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/infer", tags=["inference"])

@router.post("/", response_model=InferResponse)
async def infer_endpoint(
    request: Request,
    req: InferRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Smart Inference Endpoint.
    - Authn: Validated by Middleware (request.state.api_key)
    - Routing: Handled by InferenceService (Latency/Cost optimized)
    - Fallback: Handled by InferenceService (Retries/Failover)
    - Logging: Async DB write
    """
    try:
        # Delegate to high-level service
        # service returns ProviderResponse(text, tokens_used, latency_ms, model_used)
        result = await run_inference(req.model, req.prompt, req.max_tokens)
        
        # Async Logging
        try:
            log = RequestLog(
                provider=result.model_used,
                latency=result.latency_ms,
                token_count=result.tokens_used,
                cost=0.0, # TODO: Implement cost calculation based on provider rates
                status="success"
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            # excessive logging failure should not fail the request
            logger.error(f"Failed to log request: {e}", exc_info=True)

        return InferResponse(
            output=result.text,
            provider=result.model_used,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            model=result.model_used
        )

    except (ProviderTemporaryError, ProviderPermanentError) as e:
        logger.error(f"Inference failed: {e}")
        # Service exhausted retries/fallbacks
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal inference error")

@router.post("/", response_model=InferResponse)
async def infer_endpoint(
    req: InferRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Pass api_key_id from middleware context
    api_key_id = request.state.api_key.id
    
    result = await run_inference(
        req.model, req.prompt, req.max_tokens, 
        api_key_id, background_tasks
    )
    
    return InferResponse(...)
