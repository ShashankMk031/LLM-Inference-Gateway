import asyncio
import random
from typing import Dict, Any

async def infer(prompt: str, max_tokens: int = 256, model: str= "mock") -> Dict[str, Any]:
    # Mock LLM inference with realistic latency.
    latency_ms = random.uniform(100, 300)
    await asyncio.sleep(latency_ms / 1000) # Simulate network/processing

    # Mock response: first 50 chars + filler
    preview = prompt[:50].strip()
    output = f"This is a mock-response to : '{preview}' ,,, (truncated)"

    return {
        "output":output,
        "provider":"mock",
        "latency_ms": round(latency_ms, 2),
        "tokens_used":min(len(prompt.split()) * 2, max_tokens),
        "model":model
    }