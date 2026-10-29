"""Waiting in tests for what the controller does in the background."""

import asyncio
from collections.abc import Callable


async def until(condition: Callable[[], bool], seconds: float = 2):
    async with asyncio.timeout(seconds):
        while not condition():
            await asyncio.sleep(0.01)
