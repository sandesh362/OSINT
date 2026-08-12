# OSINT Toolkit - Phases 1–4

A modular FastAPI backend for an academic OSINT cybersecurity project. It provides public domain intelligence, Shodan-backed network reconnaissance, public username profile checks, and safe breach metadata checks through a versioned API.

```
Client
  |
  v
/api/v1 router
  |
  +-- /domain-intel router --> service --> provider client --> WHOIS / DNS
  +-- /network-recon router -> service --> provider client --> Shodan API
  +-- /social-profiling router -> async service --> public profile URLs
  +-- /breach-check router -> async service --> XposedOrNot API
                                |
                                +--> 15-minute TTL cache + 2/sec throttle
```

Each feature router is registered in `backend/app/api/v1/router.py`.

## Setup

Use Python 3.11 or newer.

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Run and test

```bash
cd backend
uvicorn app.main:app --reload
pytest
```

Endpoints:

- `GET /api/v1/domain-intel/whois?domain=example.com`
- `GET /api/v1/domain-intel/dns?domain=example.com`
- `GET /api/v1/network-recon/host?ip=1.2.3.4`
- `GET /api/v1/network-recon/search?query=product:%22Apache%20httpd%22&page=1`
- `GET /api/v1/social-profiling/username?value=someuser`
- `GET /api/v1/breach-check/email?value=someone@example.com`

Successful responses use `{ "success": true, "data": ..., "meta": { "queried_at": ... } }`.

## Breach check

`breach_check` uses the free [XposedOrNot breach-analytics API](https://xposedornot.com/api); no API key is required. Its endpoint limits are 2 requests/second, 25 requests/hour, and 100 requests/day per IP. The client self-throttles to two requests per second and caches each normalized email result for 15 minutes, so tests and demos must avoid repeated uncached lookups.

The feature returns only breach name, date, exposed data-class categories, and a short description. It never returns passwords, hashes, raw breach records, or credentials. See [Phase 4 notes](docs/phase4-notes.md) for the provider rationale, ethics boundary, cache design, and methodological guidance.

## Shodan API key

Create a Shodan account and place its API key in `backend/.env` as `SHODAN_API_KEY`. Never commit a real key. Missing or invalid keys return a generic server error; quota exhaustion returns HTTP 429.

## Authentication seam

Authentication is intentionally out of scope for Phase 1. Future security dependencies belong in `backend/app/core/security.py` and can be attached to feature routers or API versions without mixing auth logic into lookup services.

See [Phase 1 notes](docs/phase1-notes.md), [Phase 2 notes](docs/phase2-notes.md), [Phase 3 notes](docs/phase3-notes.md), and [Phase 4 notes](docs/phase4-notes.md).
