"""Read exported PDFs to verify that real report data survives rendering."""

from datetime import datetime, timezone
from io import BytesIO

from pypdf import PdfReader

from app.features.report_engine.generators.pdf_generator import PdfReportGenerator
from app.features.report_engine.router import get_report_engine_service
from app.features.report_engine.schemas import InvestigationReport, ReportSection, ReportTarget


def sample_report() -> InvestigationReport:
    return InvestigationReport(
        report_id="c9249744-0459-4bc5-a70b-d1c16bbd2df7",
        target=ReportTarget(domain="example.com"),
        generated_at=datetime(2026, 10, 15, tzinfo=timezone.utc),
        requested_modules=["domain_intel"],
        sections=[ReportSection(
            module="domain_intel", title="Domain Intelligence", status="complete",
            summary="Registration and DNS records returned.",
            data={"whois": {"registrar": "Example <Registrar> & Co"}, "dns": {"a": ["192.0.2.1"]}},
        )],
        findings=["Domain has public records."],
        limitations="Public-source results require verification.",
    )


def test_pdf_contains_identifiers_findings_and_escaped_provider_data():
    pdf = PdfReportGenerator().render(sample_report())
    reader = PdfReader(BytesIO(pdf))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "example.com" in text
    assert "Example <Registrar> & Co" in text
    assert "192.0.2.1" in text
    assert "Domain has public records." in text
    assert "Public-source results require verification." in text
    assert "Page 1" in text


def test_long_report_paginates_without_dropping_last_item():
    report = sample_report()
    report.sections[0].data = {"results": [{"description": f"Result {i} " + "long provider value " * 30} for i in range(80)]}
    reader = PdfReader(BytesIO(PdfReportGenerator().render(report)))
    assert len(reader.pages) > 1
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "Result 79" in text
    assert "Public-source results require verification." in text


def test_pdf_download_endpoint_returns_a_readable_attachment(client):
    class FakeService:
        async def generate(self, request):
            return sample_report()

        def cache_report(self, report, html):
            pass

    client.app.dependency_overrides[get_report_engine_service] = FakeService
    response = client.post("/api/v1/report-engine/generate", json={"domain": "example.com", "modules": ["domain_intel"], "format": "pdf"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert "example.com" in PdfReader(BytesIO(response.content)).pages[0].extract_text()
