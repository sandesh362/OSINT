# Phase 4 notes: breach check

## Provider choice and terms

Phase 4 uses the free [XposedOrNot breach-analytics API](https://xposedornot.com/api), an open-source breach-exposure lookup service. The selected `GET /v1/breach-analytics?email=...` endpoint needs no API key; a key would be relevant only to the out-of-scope domain-breaches endpoint. XposedOrNot's published free-tier limits for this endpoint are 2 requests/second, 25 requests/hour, and 100 requests/day per IP. Contributors must follow the provider's current terms and acceptable-use requirements. Its open-source status is useful to cite in the report's Literature Review/Tools section.

## Ethical and legal boundary

This module is only a client of the provider's existing metadata service. It never obtains, mirrors, scrapes, hosts, reconstructs, or displays breach dumps, password lists, leaked credentials, passwords, hashes, or raw breach records. It returns only the breach name, breach date, exposed data-class categories, and a short provider description. A breach indication communicates risk; it is not authorisation to access an account or proof of identity.

The queried email is the only personal data in play. It is sent to XposedOrNot for the lookup, is not logged, and is retained only as a key/value in a process-local 15-minute TTL cache. That cache is not persistent and disappears on restart.

## Throttling, cache, and errors

The client uses a process-wide `asyncio.Lock` with a 0.5-second minimum interval, independently of callers. This enforces the 2 requests/second limit before making requests instead of waiting for a 429. A 15-minute per-email TTL cache covers both breached and clean outcomes. It reduces duplicate requests during testing and demonstrations, which is especially important against the 25/hour cap; tests use fake providers and make no network requests.

Provider 429 responses become HTTP 429 with “rate limit reached, try again later.” Provider 502 and 503 responses become HTTP 503 with “breach data temporarily unavailable.” Malformed provider responses become generic HTTP 502 responses; raw responses are logged only on the server for diagnosis.

## Methodological note: clean results

`breached: false` and an empty list are valid HTTP 200 outcomes when XposedOrNot returns an all-null or empty breach payload. They mean this provider currently has no matching record, not that the address has never been exposed. Including these results avoids false-negative bias in the Results discussion and makes coverage limitations visible.
