"""Normalize feature outputs into one report model independent of export format."""

from typing import Any

from app.features.report_engine.schemas import InvestigationReport, ModuleName, ReportSection, ReportTarget
from app.shared.utils import utc_now


TITLES: dict[ModuleName, str] = {
    "domain_intel": "Domain Intelligence",
    "network_recon": "Network Reconnaissance",
    "social_profiling": "Social Profiling",
    "breach_check": "Breach Check",
}
LIMITATIONS = (
    "OSINT results are point-in-time observations and may contain false positives or false negatives. "
    "Corroborate material findings with authorised, independent sources before relying on them."
)


def make_section(module: ModuleName, status: str, data: dict[str, Any] | None = None, error: str | None = None) -> ReportSection:
    """Build a single status-aware, format-neutral report section."""
    data = data or {}
    if status == "not_requested":
        summary = "Not requested for this report."
    elif status == "skipped":
        summary = "Requested, but no applicable target input was supplied."
    elif status == "unavailable":
        summary = "The module could not complete; other report sections remain available."
    elif status == "empty":
        summary = "The module completed and returned no matching findings."
    else:
        summary = "The module completed successfully."
    return ReportSection(module=module, title=TITLES[module], status=status, summary=summary, data=data, error_message=error)


def aggregate_report(
    report_id: str,
    target: ReportTarget,
    requested_modules: list[ModuleName],
    sections: list[ReportSection],
) -> InvestigationReport:
    """Combine normalized sections and derive plain-language findings."""
    return InvestigationReport(
        report_id=report_id,
        target=target,
        generated_at=utc_now(),
        requested_modules=requested_modules,
        sections=sections,
        findings=_findings(sections),
        limitations=LIMITATIONS,
    )


def _findings(sections: list[ReportSection]) -> list[str]:
    findings: list[str] = []
    for section in sections:
        if section.status not in {"complete", "empty"}:
            continue
        if section.module == "domain_intel" and section.status == "complete":
            whois = section.data.get("whois", {})
            registrar, expiry = whois.get("registrar"), whois.get("expiration_date")
            if registrar or expiry:
                findings.append(f"Domain registrar: {registrar or 'not reported'}; expiry: {expiry or 'not reported'}.")
        elif section.module == "network_recon" and section.status == "complete":
            ports = section.data.get("open_ports", [])
            findings.append(f"Network reconnaissance detected {len(ports)} open port(s).")
        elif section.module == "social_profiling" and section.status == "complete":
            results = section.data.get("results", [])
            found = sum(result.get("status") == "found" for result in results)
            findings.append(f"Username was found on {found} of {len(results)} checked platform(s).")
        elif section.module == "breach_check":
            breaches = section.data.get("breaches", [])
            findings.append(f"Email appears in {len(breaches)} known breach(es).")
    return findings or ["No positive findings were generated from the completed modules."]
