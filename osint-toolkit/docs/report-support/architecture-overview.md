# Architecture overview

Adapt this for Methodology (4) and OSINT Tools and Techniques (2.2). The backend uses feature-based modules instead of a flat route collection: every source owns a router, service, provider client, schemas, and tests. This isolates providers, gives each OSINT source one replacement seam, and makes mocking and auditing straightforward.

```text
app/
├── api/v1/router.py
├── core/                 # settings, exceptions, logging
├── shared/               # response envelope
└── features/
    ├── domain_intel/     # WHOIS and DNS
    ├── network_recon/    # Shodan
    ├── social_profiling/ # public profile checks
    ├── breach_check/     # XposedOrNot metadata
    └── report_engine/    # aggregation and exports
```
