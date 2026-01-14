from pydantic import BaseModel,Field
from typing import Optional

class InferRequest(BaseModel):
    prompt: str = Field(...,min_length = 1, max_length=4000)
    model: str = Field("mock", pattern="^[a-zA-Z0-9_-]+$")
    max_tokens: int = Field(256, ge=1, le=4096)

class InferResponse(BaseModel):
    output:str
    provider:str="mock"
    latency_ms: float
    tokens_used: int
    model: str
