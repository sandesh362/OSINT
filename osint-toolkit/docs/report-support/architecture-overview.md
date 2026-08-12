# Architecture overview

Use this as an outline for Methodology (section 4) and OSINT Tools and Techniques (section 2.2). The backend uses feature-based modules rather than one flat collection of routes or a purely layered project. Each source has one seam—router, service, client, schemas, tests—so a provider can be tested, replaced, or isolated without altering the others.

```text
app/
├── api/v1/router.py       # feature registration and health check
├── core/                  # configuration, logging, exceptions
├── shared/                # common JSON response envelope
└── features/
    ├── domain_intel/      # WHOIS and DNS
    ├── network_recon/     # Shodan host/search
    ├── social_profiling/  # public username checks
    ├── breach_check/      # XposedOrNot metadata
    └── report_engine/     # aggregation and exports
```

This structure improves isolation, testability, and auditability: each OSINT source has one clear provider boundary, while shared concerns remain central.
