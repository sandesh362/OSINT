# Phase 6 notes: frontend dashboard

## Implementation approach

The frontend uses React 18, TypeScript, Vite, Axios, and plain global CSS. CSS
was selected over a component framework to keep the academic prototype small,
auditable, and easy to restyle for report screenshots. Features are grouped by
backend capability (`domain-intel`, `network-recon`, `social-profiling`,
`breach-check`, and `report-engine`) instead of being placed in a generic pages
directory. Shared UI elements and the `useApiCall` hook centralise loading,
error, and raw-response handling.

The single-page tab layout is intentional: it keeps each individual lookup
readable while reserving the Report Engine tab for a consolidated output useful
in the Implementation and Results screenshots. Tables are the primary result
view and a collapsible raw response is retained for debugging and demos.

## UX and backend alignment

Client validation mirrors the bounded domain, email, username, and IP inputs
accepted by the backend. API errors are converted to useful messages: 404 is
shown as no data, 429 as a short rate-limit warning, and 500/503 as service
unavailability. Report generation supports HTML iframe preview or browser PDF
download. Network reconnaissance requires an IP address because its existing
service layer exposes host lookup by IP, not domain; the report form makes that
requirement explicit rather than inventing a backend-side domain-to-IP flow.

## Known limitations

There is no authentication, multi-user isolation, client-side result history,
or persistent report storage. The report preview relies on the backend's
prototype cache. The frontend deliberately contains no provider credentials;
the backend must run separately and CORS must be configured when origins differ.
This dashboard is a lab interface and its generated report is a starting point
for the student to verify, edit, and contextualise before submission.
