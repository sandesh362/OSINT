# OSINT Toolkit - Phases 1–4

A modular FastAPI backend for an academic OSINT cybersecurity project. Phase 1
delivers `domain_intel` (public WHOIS/DNS), `network_recon`
(Shodan-backed exposed-host intelligence), and `social_profiling` (public
username profile existence checks), and `breach_check` (safe summaries from
the Have I Been Pwned breach API) through a versioned API.

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
  +-- /breach-check router -> async service --> HIBP v3 API
                                |                  |
                                +--> TTL cache      +--> serialized throttle
```

The feature boundary keeps future modules (`report_engine`) independent. Each
feature router is registered in `backend/app/api/v1/router.py`.

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
- `GET /api/v1/breach-check/email?value=someone@example.com`

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

## Breach-check provider and scope

`breach_check` uses the authenticated [Have I Been Pwned API v3](https://haveibeenpwned.com/API/v3)
because it provides established breach metadata without this project handling
breach dumps. Set `BREACH_API_KEY` in `backend/.env` to an HIBP subscription
key; email lookups require an eligible paid plan, while documented test keys
are limited to HIBP integration-test addresses. The API's attribution and
acceptable-use requirements apply. The feature returns only breach name, date,
data-class categories, and a public reference link—never passwords, hashes,
raw breach records, or credentials. It throttles requests and retains a queried
email only in its in-memory 15-minute cache; email values are not logged.

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
[Phase 3 notes](docs/phase3-notes.md), and
[Phase 4 notes](docs/phase4-notes.md) for design, methodology, and
rate-limit notes.
