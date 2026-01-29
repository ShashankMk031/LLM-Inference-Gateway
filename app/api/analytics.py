from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from typing import List, Optional
from datetime import datetime, date

from ..db.session import get_db
from ..db.base import RequestLog, APIKey
from ..auth.jwt import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user)] # Admin only
)

@router.get("/usage-by-key")
async def get_usage_by_key(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get total token usage and cost grouped by API Key ID."""
    stmt = (
        select(
            RequestLog.api_key_id,
            func.sum(RequestLog.token_count).label("total_tokens"),
            func.sum(RequestLog.cost).label("total_cost"),
            func.count(RequestLog.id).label("request_count")
        )
        .group_by(RequestLog.api_key_id)
        .order_by(desc("total_tokens"))
        .limit(limit)
    )
    
    if start_date:
        stmt = stmt.where(func.date(RequestLog.timestamp) >= start_date)
    if end_date:
        stmt = stmt.where(func.date(RequestLog.timestamp) <= end_date)
        
    result = await db.execute(stmt)
    
    # Format log
    data = []
    for row in result:
        data.append({
            "api_key_id": row.api_key_id,
            "total_tokens": row.total_tokens,
            "total_cost": round(row.total_cost, 6),
            "request_count": row.request_count
        })
    return data

@router.get("/cost-by-provider")
async def get_cost_by_provider(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get cost breakdown by provider."""
    stmt = (
        select(
            RequestLog.provider,
            func.sum(RequestLog.cost).label("total_cost"),
            func.sum(RequestLog.token_count).label("total_tokens"),
            func.count(RequestLog.id).label("request_count")
        )
        .group_by(RequestLog.provider)
        .order_by(desc("total_cost"))
    )
    
    if start_date:
        stmt = stmt.where(func.date(RequestLog.timestamp) >= start_date)
    if end_date:
        stmt = stmt.where(func.date(RequestLog.timestamp) <= end_date)
        
    result = await db.execute(stmt)
    
    data = []
    for row in result:
        data.append({
            "provider": row.provider,
            "total_cost": round(row.total_cost or 0.0, 6),
            "total_tokens": row.total_tokens or 0,
            "request_count": row.request_count
        })
    return data

@router.get("/error-summary")
async def get_error_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get error counts grouped by status."""
    stmt = (
        select(
            RequestLog.status,
            func.count(RequestLog.id).label("count")
        )
        .group_by(RequestLog.status)
        .order_by(desc("count"))
    )
    
    if start_date:
        stmt = stmt.where(func.date(RequestLog.timestamp) >= start_date)
    if end_date:
        stmt = stmt.where(func.date(RequestLog.timestamp) <= end_date)
        
    result = await db.execute(stmt)
    
    data = []
    total = 0
    details = []
    for row in result:
        details.append({"status": row.status, "count": row.count})
        total += row.count
        
    return {
        "total_requests": total,
        "breakdown": details
    }

@router.get("/requests-per-day")
async def get_requests_per_day(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Get request volume for the last N days."""
    # Postgres specific date_trunc
    stmt = (
        select(
            func.date_trunc('day', RequestLog.timestamp).label("day"),
            func.count(RequestLog.id).label("count")
        )
        .group_by("day")
        .order_by(desc("day"))
        .limit(days)
    )
    
    result = await db.execute(stmt)
    
    data = []
    for row in result:
        data.append({
            "date": row.day.date(),
            "request_count": row.count
        })
    return data
