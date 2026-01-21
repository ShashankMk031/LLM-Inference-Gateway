from fastapi import APIRouter, Request, Depends, HTTPException
from ..api.schemas import InferRequest, InferResponse
from ..providers.registry import get_provider
from ..db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import RequestLog
from sqlalchemy import insert
import asyncio
import time

router = APIRouter(prefix="/infer", tags=["inference"])

@router.post("/", response_model=InferResponse)
async def infer_endpoint(
    request: Request,
    req:InferRequest,
    db:AsyncSession=Depends(get_db)
):
    # LLM Inference endpoint via registered providers
    # Middleware already validated API key -> request.state.api_key
    try:
        provider = get_provider(req.model) 

        if not await provider.is_healthy():
            raise HTTPException(503, "Provider unhealthy")

        # Provider handles everything
        start_time = time.perf_counter()
        result = await provider.infer(req.prompt, req.max_tokens)
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Log request( bonus , matches RequestLog model)
        log = RequestLog(
            provider=provider.name,
            latency=latency_ms,
            token_count=result.tokens_used,
            cost=0.0, # Mock
            status="success"
        )
        db.add(log)
        await db.commit()
        
        # Convert to response model
        return InferResponse(
            output = result.text,
            provider = provider.name,
            latency_ms = latency_ms,
            tokens_used = result.tokens_used
        )
    except ValueError as e:
        raise HTTPException(400, str(e))