# OSINT Toolkit — Phase 1

A modular FastAPI backend for an academic OSINT cybersecurity project. Phase 1
delivers `domain_intel` (public WHOIS/DNS) and `network_recon`
(Shodan-backed exposed-host intelligence) through a versioned API.

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
```

The feature boundary keeps future modules (`network_recon`, `social_profiling`,
`breach_check`, and `report_engine`) independent. Add a feature router in
`backend/app/api/v1/router.py` when it is implemented.

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

Successful responses use `{ "success": true, "data": ..., "meta": { "queried_at": ... } }`.
Provider errors are normalized to safe 404, 502, or 504 response bodies.

## Shodan API key

Create a Shodan account at [shodan.io](https://www.shodan.io/), then copy its
API key into `backend/.env` as `SHODAN_API_KEY`. Academic/free accounts can use
a free key with limited query quota. Never commit a real key. Missing or invalid
keys return a generic server error; quota exhaustion returns HTTP 429.

## Authentication seam

Authentication is intentionally out of scope for Phase 1. Future security
dependencies belong in `backend/app/core/security.py` and can be attached to
feature routers or API versions without mixing auth logic into lookup services.

See [Phase 1 notes](docs/phase1-notes.md) and
[Phase 2 notes](docs/phase2-notes.md) for design and rate-limit notes.
