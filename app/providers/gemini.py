import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import BaseProvider, ProviderResponse, ProviderPermanentError, ProviderTemporaryError
import os
import asyncio
from typing import Any

class GeminiProvider(BaseProvider):
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL_NAME","gemini-1.5-flash")
        self.model = genai.GenerativeModel(self.model_name)
        self.timeout = int(os.getenv("GEMINI_TIMEOUT", 30))

    @property
    def name(self) -> str:
        return "gemini"
    
    @retry(
        stop = stop_after_attempt(3),
        wait = wait_exponential(multiplier=1, min=4, max=10),
        retry = retry_if_exception_type(ProviderTemporaryError)
    )

    async def infer(self, prompt: str, max_tokens: int) -> ProviderResponse:
        start = asyncio.get_event_loop().time()

        try:
            # Gemiini sync client wrapped in threadpool for async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.1
                    }
                )
            )

            text = response.text or ""
            # Gemini does not return usage-rough estimate
            tokens_used = min(len(prompt.split()) * 1.5 + 50, max_tokens)
        
        except Exception as e:
            if "invalid_argument" in str(e).lower():
                raise ProviderPermanentError(f"Invalid request: {e}")
            elif "permission_denied" in str(e).lower():
                raise ProviderPermanentError("Gemini authorization denied")
            raise ProviderTemporaryError(f"Temporary error from Gemini: {e}")

        latency_ms = (asyncio.get_event_loop().time() -start) * 1000

        return ProviderResponse(
            text=text,
            tokens_used=tokens_used,
            latency_ms=round(latency_ms, 2),
            model_used = self.model_name
        )
    
    def estimate_cost(self, tokens:int) -> float:
        # Gemini 1.5 Flash: $0.075/1M input, $0.30/1M output → avg $0.1875/1M 
        return (tokens / 1_000_000) * 0.1875 
    
    async def is_healthy(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))