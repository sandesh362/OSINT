"""Throttled adapter for XposedOrNot's public breach-analytics endpoint."""

import asyncio
from collections.abc import Callable
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import BreachRateLimitError, BreachUnavailableError, LookupProviderError
from app.core.logging import get_logger
from app.features.breach_check.schemas import BreachSummary


# XposedOrNot permits at most two requests per second for this free endpoint.
MINIMUM_REQUEST_INTERVAL_SECONDS = 0.5
logger = get_logger(__name__)


class XposedOrNotClient:
    """Retrieve public breach metadata only, never credentials or breach records."""

    _throttle_lock = asyncio.Lock()
    _next_request_at = 0.0

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Any] = asyncio.sleep,
    ) -> None:
        self.base_url = get_settings().xon_base_url.rstrip("/")
        self._client = client
        self.clock = clock
        self.sleep = sleep

    async def breaches_for_email(self, email: str) -> list[BreachSummary]:
        """Return safe public breach summaries for an email address."""
        await self._throttle()
        url = f"{self.base_url}/v1/breach-analytics"
        # A key is needed only for XposedOrNot's domain-breaches endpoint, which is out of scope.
        try:
            if self._client is not None:
                response = await self._client.get(url, params={"email": email}, timeout=10.0)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params={"email": email}, timeout=10.0)
        except httpx.HTTPError as exc:
            raise BreachUnavailableError("Breach data temporarily unavailable") from exc

        if response.status_code == 429:
            logger.warning("breach_check provider rate limit reached")
            raise BreachRateLimitError(
                "Rate limit reached, try again later",
                retry_after=self._parse_retry_after(response.headers.get("retry-after")),
            )
        if response.status_code in {502, 503}:
            raise BreachUnavailableError("Breach data temporarily unavailable")
        if response.status_code != 200:
            logger.warning("breach_check provider returned unexpected status=%s", response.status_code)
            raise LookupProviderError("Breach data temporarily unavailable")

        try:
            return self._to_summaries(response.json())
        except (TypeError, ValueError) as exc:
            self._log_malformed_response(response)
            raise LookupProviderError("Breach data temporarily unavailable") from exc

    async def _throttle(self) -> None:
        """Serialize in-process requests before they reach XposedOrNot."""
        async with self._throttle_lock:
            delay = type(self)._next_request_at - self.clock()
            if delay > 0:
                await self.sleep(delay)
            type(self)._next_request_at = self.clock() + MINIMUM_REQUEST_INTERVAL_SECONDS

    @staticmethod
    def _to_summaries(payload: Any) -> list[BreachSummary]:
        """Map the documented nested response and discard all unneeded fields."""
        if not isinstance(payload, dict):
            raise ValueError("response must be an object")
        exposed = payload.get("ExposedBreaches")
        if exposed is None:
            return []
        if not isinstance(exposed, dict):
            raise ValueError("ExposedBreaches must be an object")
        details = exposed.get("breaches_details")
        if details in (None, []):
            return []
        if not isinstance(details, list):
            raise ValueError("breaches_details must be a list")

        summaries = []
        for breach in details:
            if not isinstance(breach, dict) or not isinstance(breach.get("breach"), str):
                raise ValueError("invalid breach detail")
            summaries.append(BreachSummary(
                name=breach["breach"],
                breach_date=breach.get("xposed_date") or None,
                data_classes=XposedOrNotClient._data_classes(breach.get("xposed_data")),
                description=str(breach.get("details") or "No public description available."),
            ))
        return summaries

    @staticmethod
    def _data_classes(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
        raise ValueError("invalid xposed_data")

    @staticmethod
    def _log_malformed_response(response: httpx.Response) -> None:
        """Keep raw provider diagnostics server-side and never return them to callers."""
        logger.warning("breach_check malformed provider response body=%r", response.text)

    @staticmethod
    def _parse_retry_after(value: str | None) -> int | None:
        try:
            return max(0, int(value)) if value is not None else None
        except ValueError:
            return None
