class ProviderError(Exception):

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        retry_after: float | None = None,
    ):
        super().__init__(message)

        self.retryable = retryable
        self.retry_after = retry_after


class ProviderRateLimitError(
    ProviderError
):

    def __init__(
        self,
        message: str = (
            "Provider rate limit exceeded"
        ),
        *,
        retry_after: float | None = None,
    ):
        super().__init__(
            message,
            retryable=True,
            retry_after=retry_after,
        )


class ProviderTemporaryError(
    ProviderError
):

    def __init__(
        self,
        message: str = (
            "Temporary provider failure"
        ),
    ):
        super().__init__(
            message,
            retryable=True,
        )


class ProviderPermanentError(
    ProviderError
):

    def __init__(
        self,
        message: str = (
            "Permanent provider failure"
        ),
    ):
        super().__init__(
            message,
            retryable=False,
        )