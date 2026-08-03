"""Thin, replaceable adapter around the official Shodan SDK."""

from typing import Any, NoReturn

import shodan

from app.core.config import get_settings
from app.core.exceptions import (
    LookupNotFoundError,
    LookupProviderError,
    ShodanConfigurationError,
    ShodanRateLimitError,
)


class ShodanClient:
    """Expose only the provider calls needed by the network_recon service."""

    def __init__(self) -> None:
        api_key = get_settings().shodan_api_key.strip()
        if not api_key:
            raise ShodanConfigurationError("Shodan API is not configured")
        self._api = shodan.Shodan(api_key)

    def host(self, ip: str) -> dict[str, Any]:
        """Return Shodan's raw host record, translating provider failures."""
        try:
            return self._api.host(ip)
        except shodan.APIError as exc:
            self._raise_api_error(exc)

    def search(self, query: str, page: int) -> dict[str, Any]:
        """Return one raw Shodan search page."""
        try:
            return self._api.search(query, page=page)
        except shodan.APIError as exc:
            self._raise_api_error(exc)

    @staticmethod
    def _raise_api_error(exc: Exception) -> NoReturn:
        message = str(exc).lower()
        if "no information available" in message or "not found" in message:
            raise LookupNotFoundError("No Shodan information is available for this IP") from exc
        if "rate limit" in message or "query credits" in message:
            raise ShodanRateLimitError("Shodan request quota has been reached") from exc
        if "invalid api key" in message or "access denied" in message or "authentication" in message:
            raise ShodanConfigurationError("Shodan API configuration is invalid") from exc
        raise LookupProviderError("Shodan lookup failed") from exc
