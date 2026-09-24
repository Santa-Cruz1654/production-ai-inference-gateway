import asyncio

import pytest

from app.timeout import RequestDeadline


@pytest.mark.asyncio
async def test_request_deadline_times_out_slow_operation():

    deadline = RequestDeadline(
        timeout_seconds=1.0
    )

    with pytest.raises(TimeoutError):

        async with deadline.timeout():

            await asyncio.sleep(3.0)