import logging
from fastapi import FastAPI, Depends 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text 
from .db.session import get_db
from .db.base import Base
from .config import engine

logger = logging.getLogger(__name__)

app = FastAPI(title = "LLM Inference Gateway") 

@app.get("/") 
async def root(): 
    return {"message":"Hello, World!"}

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        if value == 1:
            return {"status": "healthy", "db": "connected"}
        else:
            return {"status": "unhealthy", "db": "disconnected", "error": "Unexpected query result"}
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return {"status": "unhealthy", "db": "disconnected", "error": str(e)} 
    
@app.on_event("startup") 
async def on_startup(): 
    # Create tables if they don't exist 
    async with engine.begin() as conn: 
        await conn.run_sync(Base.metadata.create_all) 

# A quick test endpoint 
# from sqlalchemy import insert 
# from .db.base import User 

# @app.post("/test-user")
# async def create_test_user(db: AsyncSession = Depends(get_db)):
#     stmt = insert(User).values(
#         email="test@example.com",
#         hashed_password="hashed" , 
#         is_active=True,
#     ).returning(User.id)
#     result = await db.execute(stmt) 
#     user_id = result.scalar_one() 
#     await db.commit() 
#     return {"id": user_id}