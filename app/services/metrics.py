from dataclasses import dataclass
from typing import Optional
from ..providers.base import ProviderResponse

@dataclass
class InferenceMetrics:
    api_key_id: int
    model_requested: str
    provider_used: str
    latency_ms: float
    tokens_used: int
    cost: float
    status: str = "success"  # "success" or "failure"
    error_type: Optional[str] = None # "temporary", "permanent", or None

    @classmethod
    def success(cls, api_key_id: int, model:str, provider_name: str, result: ProviderResponse) -> "InferenceMetrics":
        return cls(
            api_key_id=api_key_id,
            model_requested=model,
            provider_used=provider_name,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            cost=result.provider.estimate_cost(result.tokens_used)
        )

    @classmethod
    def failure(cls, api_key_id: int, model:str, provider_name: str,error_type: str) -> "InferenceMetrics":
        return cls(
            api_key_id=api_key_id,
            model_requested=model,
            provider_used=provider_name,
            latency_ms=0.0,
            tokens_used=0,
            cost=0.0,
            status="failure",
            error_type=error_type
        )
        