import asyncio
import random

from app.provider_errors import (
    ProviderError,
)
from app.retry import (
    RetryPolicy,
    exponential_backoff,
)
from app.schemas import (
    ProviderRequest,
    ProviderResponse,
)
from app.timeout import RequestDeadline


class ProviderExecutionService:

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
    ):
        self.retry_policy = (
            retry_policy
            or RetryPolicy()
        )

    async def execute(
        self,
        provider,
        request: ProviderRequest,
        deadline: RequestDeadline,
    ) -> ProviderResponse:

        last_error: Exception | None = None

        for attempt in range(
            1,
            self.retry_policy.max_attempts + 1,
        ):

            deadline.ensure_remaining()

            try:

                async with deadline.timeout():

                    return await provider.generate(
                        request
                    )

            except TimeoutError as exc:

                last_error = exc

                # The request's global deadline has
                # been exhausted. Do not start another
                # attempt.
                if deadline.expired():
                    break

            except ProviderError as exc:

                last_error = exc

                # Permanent provider errors should
                # never be retried.
                if not exc.retryable:
                    break

                # No attempts remaining.
                if (
                    attempt
                    >= self.retry_policy.max_attempts
                ):
                    break

                delay = self._retry_delay(
                    attempt,
                    exc,
                )

                # Never sleep beyond the request's
                # remaining deadline.
                if delay >= deadline.remaining:
                    break

                await asyncio.sleep(delay)

            except Exception as exc:

                # Unexpected errors are not automatically
                # retried. They should be surfaced.
                last_error = exc
                break

        if isinstance(
            last_error,
            TimeoutError,
        ):
            raise TimeoutError(
                "Provider request exceeded "
                "the request deadline"
            )

        if isinstance(
            last_error,
            ProviderError,
        ):
            raise last_error

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "Provider execution failed"
        )

    def _retry_delay(
        self,
        attempt: int,
        error: ProviderError,
    ) -> float:

        # Server-provided retry guidance has priority.
        if error.retry_after is not None:

            return error.retry_after

        delay = exponential_backoff(
            attempt,
            self.retry_policy,
        )

        jitter = random.uniform(
            0,
            self.retry_policy.jitter_seconds,
        )

        return delay + jitter