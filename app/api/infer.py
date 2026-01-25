from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from ..api.schemas import InferRequest, InferResponse
from ..services.inference_service import run_inference
from ..providers.base import ProviderTemporaryError, ProviderPermanentError
from ..db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import RequestLog
from ..config import AsyncSessionLocal
import logging
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/infer", tags=["inference"])

async def log_request_background(log_data: dict):
    """
    Background task to log request details to the database.
    Uses a fresh session to avoid blocking the main request/response cycle.
    """
    async with AsyncSessionLocal() as session:
        try:
            log = RequestLog(**log_data)
            session.add(log)
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to log request in background: {e}", exc_info=True)
            await session.rollback()

@router.post("/", response_model=InferResponse)
async def infer_endpoint(
    request: Request,
    req: InferRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Smart Inference Endpoint.
    - Authn: Validated by Middleware
    - Routing: Handled by InferenceService
    - Logging: Non-blocking background task
    """
    try:
        # Delegate to high-level service
        result = await run_inference(req.model, req.prompt, req.max_tokens)
        
        # Prepare log data (using result fields including potentially missing ones safely)
        # Note: result has .cost now
        log_data = {
            "provider": result.model_used,
            "latency": result.latency_ms,
            "token_count": result.tokens_used,
            "cost": getattr(result, "cost", 0.0), 
            "status": "success"
        }
        
        # Schedule the background log
        background_tasks.add_task(log_request_background, log_data)

        # Return immediately
        return InferResponse(
            output=result.text,
            provider=result.model_used,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            model=result.model_used
        )

    except (ProviderTemporaryError, ProviderPermanentError) as e:
        logger.error(f"Inference failed: {e}")
        # Log failure in background? (Optional, but good practice. 
        # Here we skip complexity as we don't have result stats)
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal inference error")
