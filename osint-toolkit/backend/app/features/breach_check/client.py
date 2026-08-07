"""Throttled adapter for the Have I Been Pwned v3 breached-account API."""

import asyncio
from collections.abc import Callable
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.core.exceptions import BreachConfigurationError, BreachRateLimitError, BreachUnavailableError
from app.core.logging import get_logger
from app.features.breach_check.schemas import BreachSummary


HIBP_API_BASE_URL = "https://haveibeenpwned.com/api/v3"
HIBP_PUBLIC_BREACH_URL = "https://haveibeenpwned.com/Breach/"
HIBP_USER_AGENT = "OSINT-Toolkit/0.1 (academic breach exposure checker)"
# A conservative interval that stays clear of lower subscription-tier limits.
MINIMUM_REQUEST_INTERVAL_SECONDS = 1.6
logger = get_logger(__name__)


class HIBPClient:
    """Retrieve only public breach metadata, never breach records or credentials."""

    _throttle_lock = asyncio.Lock()
    _next_request_at = 0.0

    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Any] = asyncio.sleep,
    ) -> None:
        self.api_key = (api_key if api_key is not None else get_settings().breach_api_key).strip()
        self._client = client
        self.clock = clock
        self.sleep = sleep

    async def breaches_for_email(self, email: str) -> list[BreachSummary]:
        """Return safe breach summaries; a provider 404 means no recorded breaches."""
        if not self.api_key:
            logger.error("breach_check provider configuration failed reason=missing_api_key")
            raise BreachConfigurationError("Breach data service is unavailable")

        await self._throttle()
        url = f"{HIBP_API_BASE_URL}/breachedAccount/{quote(email, safe='')}"
        headers = {"hibp-api-key": self.api_key, "User-Agent": HIBP_USER_AGENT}
        try:
            if self._client is not None:
                response = await self._client.get(url, headers=headers, params={"truncateResponse": "false"}, timeout=10.0)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params={"truncateResponse": "false"}, timeout=10.0)
        except httpx.HTTPError as exc:
            raise BreachUnavailableError("Breach data is temporarily unavailable") from exc

        if response.status_code == 404:
            return []
        if response.status_code in {401, 403}:
            logger.error("breach_check provider configuration failed reason=credentials_rejected status=%s", response.status_code)
            raise BreachConfigurationError("Breach data service is unavailable")
        if response.status_code == 429:
            retry_after = self._parse_retry_after(response.headers.get("retry-after"))
            raise BreachRateLimitError("Breach provider rate limit has been reached", retry_after=retry_after)
        if response.status_code >= 500:
            raise BreachUnavailableError("Breach data is temporarily unavailable")
        if response.status_code != 200:
            raise BreachUnavailableError("Breach data is temporarily unavailable")

        try:
            payload = response.json()
        except ValueError as exc:
            raise BreachUnavailableError("Breach data is temporarily unavailable") from exc
        if not isinstance(payload, list):
            raise BreachUnavailableError("Breach data is temporarily unavailable")
        return [self._to_summary(item) for item in payload if isinstance(item, dict)]

    async def _throttle(self) -> None:
        """Serialize all HIBP calls in-process before they reach the provider."""
        async with self._throttle_lock:
            delay = type(self)._next_request_at - self.clock()
            if delay > 0:
                await self.sleep(delay)
            type(self)._next_request_at = self.clock() + MINIMUM_REQUEST_INTERVAL_SECONDS

    @staticmethod
    def _to_summary(raw: dict[str, Any]) -> BreachSummary:
        name = str(raw.get("Name", "Unknown breach"))
        return BreachSummary(
            name=name,
            breach_date=raw.get("BreachDate"),
            data_classes=[str(value) for value in raw.get("DataClasses", []) if isinstance(value, str)],
            reference_url=f"{HIBP_PUBLIC_BREACH_URL}{quote(name, safe='')}",
        )

    @staticmethod
    def _parse_retry_after(value: str | None) -> int | None:
        try:
            return max(0, int(value)) if value is not None else None
        except ValueError:
            return None
