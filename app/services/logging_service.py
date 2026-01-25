from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from ..db.models.request_log import RequestLog
from ..db.session import get_db
import logging

logger = logging.getLogger(__name__)

async def log_metrics(metrics: InferenceMetrics, db: AsyncSession):
    # Fire and forget logging of metrics
    try:
        stmt = insert(RequestLog).values(**metrics.dict())
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}", exc_info=True)
        # Not raising logging can't break inference

def queue_log(metrics: InferenceMetrics, background_tasks: BackgroundTasks):
    #Background task wrapper to log metrics
    background_tasks.add_task(log_metrics, metrics, get_db().__anext__())
