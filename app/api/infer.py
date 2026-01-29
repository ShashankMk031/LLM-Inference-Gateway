from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks, Header
from ..api.schemas import InferRequest, InferResponse
from ..services.inference_service import run_inference
from ..providers.base import ProviderTemporaryError, ProviderPermanentError
from ..db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..db.base import RequestLog, IdempotencyKey
from ..config import AsyncSessionLocal
import logging
import json
from datetime import datetime, timezone
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["inference"])  # No prefix - route is /infer directly

@router.post("/infer", response_model=InferResponse)
async def infer_endpoint(
    request: Request,
    req: InferRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None)
):
    """
    Smart Inference Endpoint with Idempotency.
    - Authn: Validated by Middleware
    - Idempotency: Deduplicates requests via Idempotency-Key header
    - Routing: Handled by InferenceService
    - Logging: Non-blocking background task
    """
    api_key_id = request.state.api_key.id
    
    # 1. Idempotency Check
    if idempotency_key:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.idempotency_key == idempotency_key,
                    IdempotencyKey.api_key_id == api_key_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                if existing.response_json:
                    # Return cached response
                    cached = json.loads(existing.response_json)
                    return InferResponse(**cached)
                else:
                    # Key exists but no response => currently processing
                    # Or stuck. For now, assume concurrent processing.
                    raise HTTPException(status_code=409, detail="Request with this idempotency key is currently processing")
            
            # Create lock record
            new_key = IdempotencyKey(
                idempotency_key=idempotency_key,
                api_key_id=api_key_id,
                locked_at=datetime.now(timezone.utc)
            )
            db.add(new_key)
            await db.commit()

    try:
        # 2. Run Inference
        result = await run_inference(req.model, req.prompt, req.max_tokens, api_key_id, background_tasks)
        
        response_obj = InferResponse(
            output=result.text,
            provider=result.model_used,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            model=result.model_used
        )

        # 3. Update Idempotency Record
        if idempotency_key:
            # Fire and forget update? No, we should ensure it's saved.
            # Use separate session
            async with AsyncSessionLocal() as db:
                await db.execute(
                   update(IdempotencyKey)
                   .where(IdempotencyKey.idempotency_key == idempotency_key)
                   .values(
                       response_json=json.dumps(response_obj.model_dump()), 
                       status_code=200,
                       locked_at=None
                   )
                )
                await db.commit()
        
        return response_obj

    except (ProviderTemporaryError, ProviderPermanentError) as e:
        logger.error(f"Inference failed: {e}")
        # Cleanup idempotency key on failure so user can retry
        if idempotency_key:
             async with AsyncSessionLocal() as db:
                # Need to import delete
                from sqlalchemy import delete
                await db.execute(delete(IdempotencyKey).where(IdempotencyKey.idempotency_key == idempotency_key))
                await db.commit()
                
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal inference error")
