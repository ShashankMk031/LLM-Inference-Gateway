from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProviderResponse:
    text: str
    tokens_used: int
    latency_ms: float
    model_used: str

class BaseProvider(ABC):
    # Abstract base for all LLM providers

    @property
    @abstractmethod
    def name(self) -> str:
        # Unique identifier for provider
        pass 
    
    @abstractmethod 
    async def infer(self, prompt: str, max_tokens: int) -> ProviderResponse:
        # Generate inference response 
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        # Estimate cost based on token usage
        pass 
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        # Health check for provider 
        pass