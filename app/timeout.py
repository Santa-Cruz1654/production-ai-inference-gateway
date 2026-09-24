import asyncio


class RequestDeadline:
    """
    Represents the absolute time budget for a single request.

    The deadline uses the event loop's monotonic clock rather
    than wall-clock time.

    This allows the same deadline to be shared by future
    retry and fallback operations.
    """

    def __init__(
        self,
        timeout_seconds: float,
    ):
        loop = asyncio.get_running_loop()

        self._deadline = (
            loop.time() + timeout_seconds
        )

    @property
    def deadline(self) -> float:
        """
        Return the absolute deadline.
        """

        return self._deadline

    @property
    def remaining(self) -> float:
        """
        Return the number of seconds remaining.

        Never returns a negative value.
        """

        loop = asyncio.get_running_loop()

        return max(
            0.0,
            self._deadline - loop.time(),
        )

    def expired(self) -> bool:
        """
        Return True if the request deadline has expired.
        """

        return self.remaining <= 0.0

    def ensure_remaining(self) -> None:
        """
        Raise TimeoutError if no request time remains.
        """

        if self.expired():
            raise TimeoutError(
                "Request deadline has expired"
            )

    def timeout(self):
        """
        Return an asyncio timeout context using
        the absolute request deadline.
        """

        return asyncio.timeout_at(
            self._deadline
        )