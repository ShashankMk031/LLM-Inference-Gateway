import asyncio
import random
from .base import BaseProvider, ProviderResponse

class MockProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "mock_provider"

    async def infer(self, prompt: str, max_tokens: int) -> ProviderResponse:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(random.uniform(0.1,0.3)) 

        preview = prompt[:50].strip()
        text = f"Mock response to: '{preview}'...({max_tokens} tokens max)"

        latency_ms = (asyncio.get_event_loop().time() - start) * 1000

        cost = self.estimate_cost(min(len(prompt.split()) * 2, max_tokens))

        return ProviderResponse(
            text = text,
            tokens_used = min(len(prompt.split()) * 2, max_tokens),
            latency_ms = round(latency_ms, 2),
            model_used = "mock-model",
            cost = cost
        )

    def estimate_cost(self, tokens: int) -> float: 
        return tokens * 0.0001 
    
    async def is_healthy(self) -> bool:
        return True # Mock always healthy 