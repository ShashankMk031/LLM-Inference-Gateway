from typing import Dict , List 
from .mock import BaseProvider, MockProvider

_registry: Dict[str, BaseProvider] = { 
    "mock": MockProvider(),
}

def register_provider(name : str, provider: BaseProvider):
    # Register new provider
    _registry[name] = provider

def get_provider(name: str) -> BaseProvider:
    # Get provider by name or raise 400 error
    if name not in _registry:
        raise ValueError(f"Unknown provider: {name}")
    return _registry[name]

def list_providers():
    # List all registered providers as (name, provider) tuples
    return list(_registry.items())

# 1-Line registration : eg: register_provider("openai", OpenAIProvider()) 