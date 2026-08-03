"""Domain-specific failures raised while calling external data providers."""


class UpstreamLookupError(Exception):
    """Base exception for a failed external OSINT lookup."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LookupNotFoundError(UpstreamLookupError):
    """The requested domain or record does not exist."""


class LookupTimeoutError(UpstreamLookupError):
    """An external lookup exceeded its allotted time."""


class LookupProviderError(UpstreamLookupError):
    """An external lookup provider returned an unexpected failure."""


class ShodanConfigurationError(UpstreamLookupError):
    """Shodan is unavailable because its API key is missing or invalid."""


class ShodanRateLimitError(UpstreamLookupError):
    """Shodan rejected a request because its API quota was exhausted."""
