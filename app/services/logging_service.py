from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from ..db.base import RequestLog
from ..config import AsyncSessionLocal
from .metrics import InferenceMetrics
import logging
from dataclasses import asdict

logger = logging.getLogger(__name__)

async def log_metrics(metrics: InferenceMetrics):
    # Fire and forget logging of metrics
    async with AsyncSessionLocal() as session:
        try:
            # Drop None values to let DB defaults handle them if needed, or keep explicit
            log_data = asdict(metrics)
            # Map metrics fields to RequestLog columns if they differ
            # InferenceMetrics: api_key_id, model_requested, provider_used, latency_ms, tokens_used, cost, status, error_type
            # RequestLog: provider, latency, token_count, cost, status, timestamp(auto)
            # Warning: RequestLog model does NOT have api_key_id, model_requested, error_type.
            # We must map them or update RequestLog.
            # Current RequestLog: provider, latency, token_count, cost, status.
            
            db_log = {
                "provider": metrics.provider_used,
                "latency": metrics.latency_ms,
                "token_count": metrics.tokens_used,
                "cost": metrics.cost,
                "status": metrics.status
            }
            stmt = insert(RequestLog).values(**db_log)
            await session.execute(stmt)
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}", exc_info=True)
            await session.rollback()

def queue_log(metrics: InferenceMetrics, background_tasks: BackgroundTasks):
    #Background task wrapper to log metrics
    background_tasks.add_task(log_metrics, metrics)
