"""Unauthenticated HTTP checks for configured public profile URLs."""

from datetime import datetime
import re

import httpx

from app.core.logging import get_logger
from app.features.social_profiling.platforms import Platform
from app.features.social_profiling.schemas import PlatformResult
from app.shared.utils import utc_now


logger = get_logger(__name__)
USER_AGENT = "OSINT-Toolkit/0.1 (public-profile-existence-check)"
NOT_FOUND_MARKERS = ("page not found", "profile not found", "user not found", "not found")
TITLE_RE = re.compile(r"<title[^>]*>\s*(.*?)\s*</title>", re.IGNORECASE | re.DOTALL)
DESCRIPTION_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']*)',
    re.IGNORECASE,
)


class SocialProfilingClient:
    """Perform one conservative public-page request per configured platform."""

    def __init__(self, client: httpx.AsyncClient | None = None, timeout_seconds: float = 5.0) -> None:
        self._client = client
        self.timeout_seconds = timeout_seconds

    async def check(self, platform: Platform, username: str) -> PlatformResult:
        """Return a result; HTTP failures are deliberately represented as uncertain."""
        url = platform.profile_url(username)
        checked_at = utc_now()
        try:
            if self._client is not None:
                response = await self._client.get(url, timeout=self.timeout_seconds, follow_redirects=True)
            else:
                async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
                    response = await client.get(url, timeout=self.timeout_seconds, follow_redirects=True)
            return self._interpret(platform, url, response, checked_at)
        except (httpx.HTTPError, ValueError):
            logger.warning("social_profiling platform check failed platform=%s url=%s", platform.name, url, exc_info=True)
            return PlatformResult(platform=platform.name, url=url, status="uncertain", checked_at=checked_at)

    @staticmethod
    def _interpret(
        platform: Platform, url: str, response: httpx.Response, checked_at: datetime
    ) -> PlatformResult:
        if response.status_code in platform.not_found_statuses:
            status = "not_found"
        elif platform.check_strategy == "status_with_soft_404_marker" and 200 <= response.status_code < 300:
            # Do not guess when a platform serves a known soft-404 body with 200.
            status = "not_found" if any(marker in response.text.lower() for marker in NOT_FOUND_MARKERS) else "found"
        else:
            status = "uncertain"
        title = SocialProfilingClient._match(TITLE_RE, response.text) if status == "found" else None
        description = SocialProfilingClient._match(DESCRIPTION_RE, response.text) if status == "found" else None
        return PlatformResult(platform=platform.name, url=url, status=status, checked_at=checked_at, profile_title=title, profile_description=description)

    @staticmethod
    def _match(pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        return re.sub(r"\s+", " ", match.group(1)).strip() if match else None
