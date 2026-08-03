# Phase 2 notes: network reconnaissance

`network_recon` follows the same feature boundary as `domain_intel`: its
router handles HTTP, its service performs orchestration and audit logging, and
its client is the only Shodan-SDK import. This preserves a stable API model if
the provider changes later.

## Cache and quota considerations

Host lookups use a process-local, five-minute TTL cache keyed by IP address.
This avoids repeatedly consuming Shodan query credits when an analyst revisits
the same target during a session. Search calls are intentionally uncached:
their query and page semantics are broader and results can change more often.

Shodan academic/free keys have limited quota. The implementation caps exposed
search matches at 20 per requested page, translates quota failures to HTTP 429,
and logs every success/failure with the feature and target. A production phase
could add shared caching, user-level rate limits, and metrics; the in-process
cache is deliberately lightweight for this mini project.

## Methodology notes

Shodan is an external observation source, not a live port scan. Results should
be reported with the returned `last_updated` timestamp and interpreted as
historical exposure evidence. This distinction and the cache/quota limits are
useful caveats for the Methodology and Results sections.
