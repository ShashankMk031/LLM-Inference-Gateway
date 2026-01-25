from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from sqlalchemy import String, Integer , Float, DateTime, Enum, func
from typing import Optional
from enum import Enum as PyEnum

class LogStatus(str, PyEnum):
    success = "success"
    failure = "failure"

class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(primary_key = True, index = True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), index = True)
    model_requested: Mapped[str] = mapped_column(String(50), index = True) # "auto", "opnenai" 
    provider_used: Mapped[str] = mapped_column(String(50), index = True) # Actual provider
    latency_ms: Mapped[float] = mapped_column(Float)
    tokens_used: Mapped[int] = mapped_column(Integer)
    cost: Mapped[float] = mapped_column(Float, default = 0.0)
    status: Mapped[LogStatus] = mapped_column(default = LogStatus.success)
    error_type: Mapped[Optional[str]] = mapped_column(String(100)) # temproray/permanent/none
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default= func.now())

    # Relationships
    api_key: Mapped["APIKey"] = relationship(back_populates="logs")