from groq import (
    APIConnectionError,
    APIStatusError,
    AsyncGroq,
    RateLimitError,
)

from app.provider_errors import (
    ProviderPermanentError,
    ProviderRateLimitError,
    ProviderTemporaryError,
)
from app.providers.base import LLMProvider
from app.schemas import ProviderRequest, ProviderResponse


class GroqProvider(LLMProvider):

    def __init__(self, api_key: str):
        self.client = AsyncGroq(
            api_key=api_key,
            max_retries=0,
        )

    async def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:

        try:

            response = (
                await self.client.chat.completions.create(
                    model=request.model,
                    messages=[
                        {
                            "role": "user",
                            "content": request.prompt,
                        }
                    ],
                    temperature=request.temperature,
                    max_completion_tokens=request.max_tokens,
                    reasoning_effort="low",
                    include_reasoning=False,
                )
            )

        except RateLimitError as exc:

            retry_after = None

            if exc.response is not None:
                value = exc.response.headers.get(
                    "retry-after"
                )

                if value:
                    try:
                        retry_after = float(value)
                    except ValueError:
                        retry_after = None

            raise ProviderRateLimitError(
                retry_after=retry_after,
            ) from exc

        except APIConnectionError as exc:

            raise ProviderTemporaryError(
                "Provider connection failed"
            ) from exc

        except APIStatusError as exc:

            if exc.status_code >= 500:

                raise ProviderTemporaryError(
                    f"Provider returned HTTP "
                    f"{exc.status_code}"
                ) from exc

            raise ProviderPermanentError(
                f"Provider returned HTTP "
                f"{exc.status_code}"
            ) from exc

        text = (
            response.choices[0]
            .message
            .content
            or ""
        )

        return ProviderResponse(
            text=text,
        )