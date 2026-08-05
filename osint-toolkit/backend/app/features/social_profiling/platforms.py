"""Declarative public-profile endpoints supported by social profiling.

Only unauthenticated, public profile URL patterns belong here.  A platform can
be added or removed without changing the HTTP client or service orchestration.
"""

from dataclasses import dataclass
from typing import Literal


CheckStrategy = Literal["status_with_soft_404_marker"]


@dataclass(frozen=True, slots=True)
class Platform:
    """Configuration for a public username profile endpoint."""

    name: str
    url_template: str
    check_strategy: CheckStrategy = "status_with_soft_404_marker"
    not_found_statuses: frozenset[int] = frozenset({404})

    def profile_url(self, username: str) -> str:
        return self.url_template.format(username=username)


# These endpoints are intentionally limited to public, unauthenticated profile
# pages whose usual absence signal is HTTP 404.  Ambiguous responses are never
# treated as evidence that an account exists.
PLATFORMS: tuple[Platform, ...] = (
    Platform("GitHub", "https://github.com/{username}"),
    Platform("GitLab", "https://gitlab.com/{username}"),
    Platform("Reddit", "https://www.reddit.com/user/{username}"),
    Platform("Twitch", "https://www.twitch.tv/{username}"),
    Platform("Medium", "https://medium.com/@{username}"),
    Platform("DEV Community", "https://dev.to/{username}"),
    Platform("Keybase", "https://keybase.io/{username}"),
    Platform("Codeberg", "https://codeberg.org/{username}"),
)
