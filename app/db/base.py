from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String , Integer , Boolean, Float, DateTime, func, ForeignKey

class Base(AsyncAttrs, DeclarativeBase):
    pass # All models will inherit from this base class 

class User(Base): 
    __tablename__ = "users" 

    id: Mapped[int] = mapped_column(primary_key = True, index = True) 
    email: Mapped[str] = mapped_column(String(255), unique = True, index = True) 
    hashed_password: Mapped[str] = mapped_column(String(255)) 
    is_active: Mapped[bool] = mapped_column(Boolean, server_default = "true")

class APIKey(Base): 
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key = True, index = True)
    key_hash: Mapped[str] = mapped_column(String(255), unique = True, index = True) 
    rate_limit: Mapped[int] = mapped_column(Integer) # requests/minute, etc 
    active: Mapped[bool] = mapped_column(Boolean, server_default = "true")
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for migration; set NOT NULL after backfill

class RequestLog(Base): 
    __tablename__ = "request_logs" 

    id: Mapped[int] = mapped_column(primary_key = True, index = True) 
    provider : Mapped[str] = mapped_column(String(100)) # eg : "openai", "groq", etc
    latency: Mapped[float] = mapped_column(Float) # eg : ms or seconds 
    token_count: Mapped[int] = mapped_column(Integer) 
    cost: Mapped[float] = mapped_column(Float) # eg: In ₹ or $ 
    status: Mapped[str] = mapped_column(String(50)) # eg: "success", "failure"
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone = True), 
        server_default = func.now()
    )