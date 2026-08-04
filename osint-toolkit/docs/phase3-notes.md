# Phase 3 notes: social profiling design

## Status and scope

Phase 3 is the planned `social_profiling` feature. This document records its
design and methodology boundary only; it does **not** add a social-profiling
API or collect data yet. The implementation should begin only after its data
sources, permitted use, and retention rules have been agreed for the academic
project.

The intended purpose is to correlate publicly available profile indicators
from user-supplied identifiers, such as a username or a public profile URL.
It must not attempt credential access, private-data collection, account
enumeration intended to harass individuals, or circumvention of site controls.

## Planned module boundary

The feature should follow the established layout exactly:

```text
app/features/social_profiling/
|-- router.py       # /social-profiling HTTP namespace only
|-- service.py      # orchestration, normalisation, audit logs
|-- client.py       # provider SDKs or approved HTTP adapters only
|-- schemas.py      # validated request and stable response models
`-- tests/          # mocked provider tests; no live social-platform calls
```

`app/api/v1/router.py` should register the completed router with one
`include_router` call. Shared envelopes, logger setup, configuration, and
exception handlers should be reused rather than duplicated.

## Proposed data flow

```text
Validated identifier
        |
        v
social_profiling router -> service -> approved provider clients
                              |
                              +-> normalised public indicators + audit log
```

The service should return provider-neutral fields, for example a source name,
public profile URL, display name when public, verification state when supplied
by the source, and collection timestamp. It should label each observation with
its source and should not infer identity merely because usernames match.

## Safety, privacy, and ethics

- Collect only public data permitted by the source's terms and API policy.
- Require a declared, authorised investigation or research purpose from the
  operator before a future production deployment.
- Minimise data returned and retained; do not persist raw profile data by
  default in this academic prototype.
- Do not expose secrets, access tokens, or provider error details in API
  responses or logs.
- Treat a username match as a lead, not proof that two accounts belong to the
  same person.
- Provide clear provenance and timestamps so findings can be independently
  reviewed or removed where appropriate.

## Reliability and rate-limit strategy

Social platforms often enforce stricter quotas and changing access policies
than DNS or Shodan. Each provider client should have explicit timeouts,
provider-specific error translation, a conservative request budget, and a
short TTL cache for repeated lookups. The service should return partial results
with source-level status where that is safe and useful, while logging failures
without leaking provider credentials or raw error text.

Testing must use fixture payloads and mocked clients. Required scenarios should
include valid public results, malformed identifiers, unavailable profiles,
provider authentication failure, rate limiting, partial provider failure, and
response-envelope consistency.

## Methodology and results guidance

For the mini-project report, describe the feature as public-source discovery,
not identity verification. Record the query type, collection time, source,
result count, and known limitations. Evaluate results using precision-oriented
examples: false positives from shared usernames, missing data from private
profiles, delayed indexing, and changes in platform policies.

The comparison with existing methods should focus on the benefit of a modular,
auditable workflow: one API contract, isolated provider adapters, predictable
failure handling, and no live external calls in the test suite.
