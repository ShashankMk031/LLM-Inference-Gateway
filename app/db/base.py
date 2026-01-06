from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String , Integer , Boolean, Float, DateTime, func

class Base(AsyncAttrs, DeclarativeBase):
    pass # All models will inherit from this base class 

class User(Base): 
    __tablename__ = "users" 

    id: Mapped[int] = mapped_column(primary_key = True, index = True) 
    email: Mapped[str] = mapped_column(String(255), unique = True, index = True) 
    hashed_password: Mapped[str] = mapped_column(String(255)) 
    is_active: Mapped[bool] = mapped_column(Boolean, default = True) 

class APIKey(Base): 
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key = True, index = True)
    key_hash: Mapped[str] = 