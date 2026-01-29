# Central registry for all providers
from .openai import OpenAIProvider
from .gemini import GeminiProvider

# Singleton instances - only OpenAI and Gemini
_providers = {
    "openai": OpenAIProvider(),
    "gemini": GeminiProvider(),
}

def get_provider(name: str):
    """Get provider by name. Raises ValueError if not found."""
    if name not in _providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(_providers.keys())}")
    return _providers[name]

def get_all_providers():
    """Get all registered providers."""
    return list(_providers.values())