import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any
from .base import BaseProvider , ProviderResponse
import os
import asyncio
from datetime import datetime

class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=int(os.getenv("OPENAI_TIMEOUT", 30)),
            max_retries=0 # Handled manually
        )
        self.model=os.getenv("OPENAI_MODEL","gpt-4o-mini")

    @property
    def name(self) -> str:
        return "openai"
    
    @retry(
        stop=stop_after_attempt(3),
        wait= wait_exponential(multiplier=1, min=1, max=10),
        retry = retry_if_exception_type((openai.APIConnectionError, openai.RateLimitError))
    )

    async def infer(self,prompt: str, max_tokens:int) -> ProviderResponse:
        start=asyncio.get_event_loop().time()
        try:
            response= await self.client.chat.completions.create(
                model = self.model,
                messages = [{"role":"user", "content":prompt}],
                max_tokens = max_tokens,
                temperature = 0.1
            )

            choice = response.choices[0]
            text = choice.message.content or ""
            tokens_used = (
                choice.finish_reason == "length" and max_tokens
                or getattr(response.usage, 'total_tokens', len(prompt.spilt()) * 2)
            )

            except openai.BadRequestError :
                raise ValueError(f"Invalid request for model {self.model}")
            except (openai.AuthenticationError, openai.PermissionDeniedError):
                raise ValueError("OpenAI auth/confid invalid")
            except openai.APITimeoutError:
                raise RuntimeError("OpenAI Timeout")
            
            latency_ms = (aysncio.get_event_loop().time() - start) * 1000

            return ProviderResponse(
                text=text,
                tokens_used =tokens_used,
                latency_ms=round(latency_ms,2),
                model_used = self.model
            )
        
        def estimate_cost(self, tokens: int) -> float:
            # GPT-4o-mini cost estimation : : $0.15/1M input, $0.60/1M output → avg $0.375/1M
            return (tokens / 1_000_000) * 0.375
        
        async def is_healthy(self) -> bool:
            return bool(os.getenv("OPENAI_API_KEY"))