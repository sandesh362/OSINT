# Phase 4 notes: breach check

## Provider choice and terms

Phase 4 uses the Have I Been Pwned (HIBP) API v3 `breachedAccount` endpoint.
It is a reputable, purpose-built source that returns breach metadata without
requiring this academic project to download or operate breach databases. Email
search requires an HIBP subscription key (`BREACH_API_KEY`) and an identifying
User-Agent. HIBP publishes constrained test addresses and test-key guidance,
but normal email lookup requires an eligible subscription plan.

The implementation must comply with HIBP's acceptable-use and attribution
requirements: it identifies HIBP as the data source, does not query for harm,
does not attempt to bypass controls, and does not present HIBP data as its own.
See the official [HIBP API documentation](https://haveibeenpwned.com/API/v3)
for the current endpoint, plan, attribution, and rate-limit terms.

## Ethical and legal boundary

The module is only a client of HIBP. It never obtains, mirrors, scrapes,
hosts, reconstructs, or displays breach dumps, leaked passwords, hashes, or
credential records. Its output is strictly a public metadata summary: breach
name, breach date, exposed data-class categories, and an HIBP public reference
link. A breach indication is risk information, not authorisation to access an
account or confirmation of identity.

The queried email is the only personal data used. It is sent to HIBP as
required by the selected endpoint, is never written to application logs, and
is retained only as a key/value in the process-local 15-minute TTL cache. The
cache is not persistent and is lost on process restart. API keys are read from
environment configuration and are neither logged nor returned.

## Throttling, errors, and cache

Every HIBP request passes through a process-wide `asyncio.Lock` and a minimum
1.6-second interval. This serializes calls before they reach the provider,
rather than reacting only after a 429. A provider 429 is still surfaced as HTTP
429 with its `retry_after` value when supplied. Missing or rejected credentials
become a generic HTTP 500; provider timeouts and service failures become HTTP
503 without provider internals.

Successful results, including clean results, are cached per normalized email
for 15 minutes. This avoids wasteful repeat calls during a demonstration or
report-writing session and reduces the likelihood of exhausting a subscription
quota. Tests replace the provider entirely; no test needs an API key or makes a
network request.

## Methodological note: clean results

`breached: false` is a valid result and returns HTTP 200 with an empty breach
list. It means no records were returned by the selected provider under its
current coverage and policy; it does not prove an address has never been
exposed. Reporting clean results alongside positive results avoids a
false-negative bias in the Results discussion and makes coverage limitations
visible.
