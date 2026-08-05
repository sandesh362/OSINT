"""Concurrent orchestration and short-lived caching for username checks."""

import asyncio
from collections.abc import Callable
import time
from typing import Protocol

from app.core.logging import get_logger
from app.features.social_profiling.client import SocialProfilingClient
from app.features.social_profiling.platforms import PLATFORMS, Platform
from app.features.social_profiling.schemas import PlatformResult, UsernameLookupData


logger = get_logger(__name__)
USERNAME_CACHE_TTL_SECONDS = 600.0
MAX_CONCURRENT_CHECKS = 5
_username_cache: dict[str, tuple[float, UsernameLookupData]] = {}


class ProfileChecker(Protocol):
    async def check(self, platform: Platform, username: str) -> PlatformResult: ...


class SocialProfilingService:
    """Check public profile URLs in parallel without allowing a single failure to abort a query."""

    def __init__(
        self,
        client: ProfileChecker | None = None,
        platforms: tuple[Platform, ...] = PLATFORMS,
        cache: dict[str, tuple[float, UsernameLookupData]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client or SocialProfilingClient()
        self.platforms = platforms
        self.cache = _username_cache if cache is None else cache
        self.clock = clock

    async def username(self, value: str) -> UsernameLookupData:
        cached = self.cache.get(value)
        if cached and cached[0] > self.clock():
            logger.info("social_profiling query succeeded target=%s source=cache", value)
            return cached[1]

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)

        async def limited_check(platform: Platform) -> PlatformResult:
            async with semaphore:
                return await self.client.check(platform, value)

        results = list(await asyncio.gather(*(limited_check(platform) for platform in self.platforms)))
        data = UsernameLookupData(username=value, results=results)
        self.cache[value] = (self.clock() + USERNAME_CACHE_TTL_SECONDS, data)
        logger.info("social_profiling query succeeded target=%s source=platforms", value)
        return data
