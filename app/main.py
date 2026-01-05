import logging
from fastapi import FastAPI, Depends 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text 
from .db.session import get_db
from .db.base import Base

logger = logging.getLogger(__name__)

app = FastAPI(title = "LLM Inference Gateway") 

@app.get("/") 
async def root(): 
    return {"message":"Hello, World!"}
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        if value == 1:
            return {"status": "healthy", "db": "connected"}
        else:
            return {"status": "unhealthy", "db": "disconnected", "error": "Unexpected query result"}
    except Exception as e:
        return {"status": "unhealthy", "db": "disconnected", "error": str(e)}
            return {"status": "healthy", "db": "connected"}
    except Exception:
        logger.error("Health check failed", exc_info=True)
        return {"status": "unhealthy", "db": "disconnected", "error": "Database connection failed"}