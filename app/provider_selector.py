from app.providers.base import LLMProvider
from app.providers.registry import ProviderRegistry


class ProviderSelector:

    def __init__(
        self,
        registry: ProviderRegistry,
    ):
        self.registry = registry

    def select(
        self,
        provider_name: str,
    ) -> LLMProvider:

        return self.registry.get(
            provider_name
        )