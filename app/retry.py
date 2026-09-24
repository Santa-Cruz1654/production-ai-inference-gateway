from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:

    max_attempts: int = 3

    base_delay_seconds: float = 1.0

    max_delay_seconds: float = 8.0

    jitter_seconds: float = 0.25


def exponential_backoff(
    attempt: int,
    policy: RetryPolicy,
) -> float:

    delay = (
        policy.base_delay_seconds
        * (2 ** (attempt - 1))
    )

    return min(
        delay,
        policy.max_delay_seconds,
    )