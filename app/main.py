from fastapi import FastAPI, Depends 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text 
from .db.session import get_db
from .db.base import Base

app = FastAPI(title = "LLM Inference Gateway") 

@app.get("/") 
async def root(): 
    return {"message":"Hello, World!"}

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    result.scalar()
    return {"status": "healthy", "db": "connected"}