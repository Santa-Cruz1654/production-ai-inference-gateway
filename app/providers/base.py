from abc import ABC, abstractmethod

from app.schemas import ProviderRequest, ProviderResponse


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        raise NotImplementedError