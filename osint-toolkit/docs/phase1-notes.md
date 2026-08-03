# Phase 1 notes

The backend is feature-first: each OSINT capability owns its router, service,
provider client, schemas, and tests. API v1 aggregates feature routers, so a
future module only needs an import and `include_router` call in
`backend/app/api/v1/router.py`.

`client.py` is the sole importer of `python-whois` and `dnspython`. The service
owns orchestration and audit-style query logs, while the router remains limited
to HTTP parsing and response construction. Provider exceptions are translated
to application exceptions and centralized handlers turn them into safe JSON
errors.

## Running

From `backend/`, create and activate a Python 3.11+ virtual environment, then:

```bash
pip install -r requirements.txt
copy .env.example .env  # Windows; use cp on macOS/Linux
uvicorn app.main:app --reload
pytest
```

This project intentionally uses `pip` and a checked-in `requirements.txt` for
a simple, portable academic-project setup.

## Rate-limit-friendly design

External WHOIS and DNS systems should be treated as scarce providers. A later
phase should add per-client request limits, short-lived cache entries keyed by
domain and record type, bounded retries with exponential backoff, and provider
timeouts. The current DNS timeout settings are environment-configurable; tests
mock the provider boundary and never issue real network requests.
