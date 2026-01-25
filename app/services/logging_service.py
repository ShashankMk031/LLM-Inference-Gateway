from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from ..db.models.request_log import RequestLog
from ..db.session import get_db
from .metrics import InferenceMetrics
import logging

logger = logging.getLogger(__name__)

async def log_metrics(metrics: InferenceMetrics):
    # Fire and forget logging of metrics
    db: AsyncSession = await get_db().__anext__()
    try:
        stmt = insert(RequestLog).values(**metrics.dict())
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}", exc_info=True)
        await db.rollback()
    finally:
        await db.close()

def queue_log(metrics: InferenceMetrics, background_tasks: BackgroundTasks):
    #Background task wrapper to log metrics
    background_tasks.add_task(log_metrics, metrics)
