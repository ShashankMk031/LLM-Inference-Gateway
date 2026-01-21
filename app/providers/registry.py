from typing import Dict , List 
from .mock import MockProvider

_registry: Dict[str, BaseProvider] = { 
    "mock": MockProvider(),
}

def register_provider(name : str, provider: BaseProvider):
    # Register new provider
    _registry[name] = provider

def get_provider(name: str) -> BaseProvider:
    # Get provider by name or raise 400 error
    if name not in _registry:
        raise ValueError(f" Unknown provider: {name}")
    return _registry[name]

def list_providers() -> List[Dict[str, str]]:
    # List all registered providers
    return [{"name": p.name} for p in _registry.values()] 

# 1-Line registration : eg: register_provider("openai", OpenAIProvider()) 