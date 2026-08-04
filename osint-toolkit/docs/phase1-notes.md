# Phase 1 notes: domain intelligence foundation

## Scope and outcome

Phase 1 established the backend conventions used by every OSINT feature and
implemented the `domain_intel` vertical slice. It exposes public WHOIS and DNS
data through versioned FastAPI endpoints:

- `GET /api/v1/domain-intel/whois?domain=example.com`
- `GET /api/v1/domain-intel/dns?domain=example.com`

The feature returns registrar, registration dates, name servers, and a public
registrant organisation where available. DNS responses include A, AAAA, MX, NS,
and TXT records. The system does not attempt to bypass privacy protection or
retrieve non-public registrant data.

## Architecture decisions

Each feature is self-contained under `app/features/<feature_name>/`:

```text
HTTP router -> service -> provider client -> external data provider
                 |
                 +-> central audit-style logger
```

- `router.py` validates HTTP input and returns the shared response envelope.
- `service.py` owns orchestration and records successful or failed queries.
- `client.py` is the only layer that imports `python-whois` and `dnspython`.
- `schemas.py` defines request validation and stable API response models.
- `tests/` mocks the client boundary, so tests do not query public services.

The API v1 router aggregates feature routers. Adding a future feature requires
one `include_router` call, without changing existing feature behavior.

## Validation, error handling, and audit trail

Domain input is normalised and checked against a basic public-domain format;
obviously malformed values return HTTP 422. Successful responses follow the
shared envelope:

```json
{
  "success": true,
  "data": {},
  "meta": {"queried_at": "2026-08-04T00:00:00Z"}
}
```

Provider failures are converted to safe, predictable HTTP responses rather
than raw stack traces: unavailable records map to 404, provider failures to
502, and timeouts to 504. The centralized logger records the feature, target,
outcome, and timestamp, providing a reproducible account of the data
collection process for the project report.

## Running and verification

From `backend/`, use Python 3.11+ and run:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

In a separate terminal, run all isolated tests:

```bash
pytest
```

The repository uses `pip` and a checked-in `requirements.txt` to keep the
academic-project setup simple and portable.

## Rate-limit and data-quality considerations

WHOIS and DNS providers are external, rate-sensitive sources. Tests always mock
providers, and the runtime has configurable DNS timeout settings. A production
deployment should add per-client rate limits, short-lived caching keyed by
domain and record type, bounded retries with exponential backoff, and metrics.

DNS and WHOIS results are point-in-time observations: DNS may vary by resolver
or location, records may be absent, and WHOIS fields can be redacted or stale.
These limitations should be stated when interpreting results in the
Methodology and Results sections.
