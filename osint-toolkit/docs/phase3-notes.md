# Phase 3 notes: social profiling

## Scope and ethics

Phase 3 adds `social_profiling`, a conservative public-source discovery
feature. Given an exact, safely validated username, it requests only the
configured public profile URL for each platform. It reports `found`,
`not_found`, or `uncertain`; when trivially present in the same public page it
may also return the HTML title and description.

The module never logs in, uses authenticated or private APIs, bypasses an
authentication wall, collects private posts/followers/DMs, or uses password
reset, recovery, email, or phone flows to enumerate accounts. It does not
persist profile content. Exact username matches are not treated as proof that
accounts belong to the same individual. These limits keep the mini-project
focused on minimal public indicators rather than identity resolution.

## Design

The implementation follows the existing feature boundary:

```text
router -> service -> client -> configured public profile URL
             |          |
             |          +-- one timeout-bounded unauthenticated GET
             +-- semaphore-capped asyncio.gather + 10-minute TTL cache
```

`platforms.py` contains small `Platform` configuration objects (name, URL
template, check strategy, and usual not-found status) so adding or removing a platform does
not spread platform-specific details through the service. This makes the
feature straightforward to compare with monolithic username-checking tools:
sources are declarative, the API contract is stable, and failures are isolated.

## Result interpretation and reliability

A configured not-found HTTP status (normally 404) yields `not_found`. A 2xx
response yields `found` unless its HTML contains a simple known not-found
marker, in which case it is treated as a soft 404. Redirects, access controls,
rate limits, malformed responses, connection failures, and timeouts yield
`uncertain`; the service deliberately does not guess.

Each request has a five-second timeout and no retries. Checks run concurrently
behind a semaphore of five, limiting total latency without hammering platforms.
The service caches a completed username result for ten minutes, which avoids
repeat traffic during demonstrations and report screenshots. All tests use
`httpx.MockTransport`; no test makes a live platform request.
