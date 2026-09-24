import time
from collections import defaultdict

from fastapi import Depends, HTTPException, status

from app.authorization import require_user


WINDOW_SECONDS = 60
MAX_REQUESTS = 5

_request_counts: dict[str, list[float]] = defaultdict(list)


def require_rate_limit(
    client: dict = Depends(require_user),
) -> dict:

    client_id = client["client_id"]
    now = time.time()

    timestamps = _request_counts[client_id]

    # Remove timestamps outside the current window.
    timestamps[:] = [
        timestamp
        for timestamp in timestamps
        if now - timestamp < WINDOW_SECONDS
    ]

    if len(timestamps) >= MAX_REQUESTS:
        retry_after = int(
            WINDOW_SECONDS - (now - timestamps[0])
        ) + 1

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(retry_after),
            },
        )

    timestamps.append(now)

    return client