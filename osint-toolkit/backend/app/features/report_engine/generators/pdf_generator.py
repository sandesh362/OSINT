"""WeasyPrint conversion of rendered report HTML to a PDF byte stream."""


class PdfReportGenerator:
    """Keep the optional PDF-rendering dependency isolated from orchestration."""

    def render(self, html: str) -> bytes:
        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise RuntimeError("WeasyPrint is required for PDF report export") from exc
        return HTML(string=html).write_pdf()
