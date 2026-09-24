from app.providers.base import LLMProvider


class ProviderRegistry:

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}

    def register(
        self,
        name: str,
        provider: LLMProvider,
    ) -> None:

        self._providers[name] = provider

    def get(
        self,
        name: str,
    ) -> LLMProvider:

        provider = self._providers.get(name)

        if provider is None:
            raise ValueError(
                f"Provider '{name}' is not registered"
            )

        return provider