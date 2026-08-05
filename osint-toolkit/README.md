# OSINT Toolkit - Phases 1–3

A modular FastAPI backend for an academic OSINT cybersecurity project. Phase 1
delivers `domain_intel` (public WHOIS/DNS), `network_recon`
(Shodan-backed exposed-host intelligence), and `social_profiling` (public
username profile existence checks) through a versioned API.

```
Client
  |
  v
/api/v1 router
  |
  +-- /domain-intel router --> service --> provider client --> WHOIS / DNS
  +-- /network-recon router -> service --> provider client --> Shodan API
                                 |                 |
                                 +--> audit logs    +--> TTL host cache
  +-- /social-profiling router -> async service --> public profile URLs
                                      |                 |
                                      +--> TTL cache    +--> capped concurrency
```

The feature boundary keeps future modules (`breach_check` and `report_engine`)
independent. Each feature router is registered in `backend/app/api/v1/router.py`.

## Setup

This repository uses `pip` with `requirements.txt` to keep setup explicit and
portable. Use Python 3.11 or newer.

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Adjust optional timeout/log settings in `.env`; documented defaults are in
`.env.example`.

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

Successful responses use `{ "success": true, "data": ..., "meta": { "queried_at": ... } }`.
Provider errors are normalized to safe 404, 502, or 504 response bodies.

## Social profiling scope and ethics

`social_profiling` checks only exact usernames against configurable public
profile URL patterns in `backend/app/features/social_profiling/platforms.py`.
It makes a single unauthenticated HTTP request per platform and returns only
`found`, `not_found`, or `uncertain`, plus a public page title/description when
trivially available. It never logs in, accesses private APIs or content,
bypasses authentication, checks password-recovery flows, or tries to determine
whether an email address or phone number is linked to an account. A matching
username is a lead, not identity proof.

## Shodan API key

Create a Shodan account at [shodan.io](https://www.shodan.io/), then copy its
API key into `backend/.env` as `SHODAN_API_KEY`. Academic/free accounts can use
a free key with limited query quota. Never commit a real key. Missing or invalid
keys return a generic server error; quota exhaustion returns HTTP 429.

## Authentication seam

Authentication is intentionally out of scope for Phase 1. Future security
dependencies belong in `backend/app/core/security.py` and can be attached to
feature routers or API versions without mixing auth logic into lookup services.

See [Phase 1 notes](docs/phase1-notes.md),
[Phase 2 notes](docs/phase2-notes.md), and
[Phase 3 notes](docs/phase3-notes.md) for design, methodology, and
rate-limit notes.
