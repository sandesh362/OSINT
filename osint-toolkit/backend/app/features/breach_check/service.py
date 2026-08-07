"""Breach-check orchestration with in-memory, short-lived email caching."""

from collections.abc import Callable
import time
from typing import Protocol

from app.core.logging import get_logger
from app.features.breach_check.client import HIBPClient
from app.features.breach_check.schemas import BreachCheckData, BreachSummary


logger = get_logger(__name__)
BREACH_CACHE_TTL_SECONDS = 900.0
_breach_cache: dict[str, tuple[float, BreachCheckData]] = {}


class BreachProvider(Protocol):
    async def breaches_for_email(self, email: str) -> list[BreachSummary]: ...


class BreachCheckService:
    """Expose safe breach summaries while keeping email values out of logs."""

    def __init__(
        self,
        client: BreachProvider | None = None,
        cache: dict[str, tuple[float, BreachCheckData]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client or HIBPClient()
        self.cache = _breach_cache if cache is None else cache
        self.clock = clock

    async def email(self, value: str) -> BreachCheckData:
        cached = self.cache.get(value)
        if cached and cached[0] > self.clock():
            logger.info("breach_check query succeeded source=cache")
            return cached[1]

        breaches = await self.client.breaches_for_email(value)
        data = BreachCheckData(value=value, breached=bool(breaches), breaches=breaches)
        self.cache[value] = (self.clock() + BREACH_CACHE_TTL_SECONDS, data)
        logger.info("breach_check query succeeded source=hibp")
        return data
