# Tools and sources summary

| Module | Tool/API/library | Contribution | Access constraint |
|---|---|---|---|
| domain_intel | `python-whois` | Registrar and registration dates | Public data; coverage varies |
| domain_intel | `dnspython` | DNS A, AAAA, MX, NS, TXT records | Resolver timeouts apply |
| network_recon | Shodan SDK/API | Host exposure and search metadata | API key and quota required |
| social_profiling | `httpx` public HTTP checks | Exact public username page observations | No login; platform behaviour varies |
| breach_check | XposedOrNot API | Breach names, dates, data categories | No key; 2/sec, 25/hour, 100/day |
| report_engine | Jinja2/WeasyPrint stack | Aggregated HTML/PDF report | In-memory, temporary output |
