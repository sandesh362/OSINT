"""Portable PDF rendering from normalized reports, without native HTML libraries."""

from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.features.report_engine.schemas import InvestigationReport


FONT_DIRECTORY = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("ReportSans", str(FONT_DIRECTORY / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(FONT_DIRECTORY / "VeraBd.ttf")))
pdfmetrics.registerFontFamily("ReportSans", normal="ReportSans", bold="ReportSans-Bold")


class PdfReportGenerator:
    """Render the same report data as HTML using paginated, wrapping flowables."""

    def render(self, report: InvestigationReport) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, leftMargin=44, rightMargin=44,
            topMargin=42, bottomMargin=48,
            title="OSINT Toolkit Investigation Report", author="OSINT Toolkit",
        )
        styles = getSampleStyleSheet()
        body = ParagraphStyle(
            "ReportBody", parent=styles["BodyText"], fontName="ReportSans",
            fontSize=9, leading=14, textColor=colors.HexColor("#1e293b"),
            spaceAfter=6, splitLongWords=True,
        )
        heading = ParagraphStyle(
            "ReportHeading", parent=body, fontName="ReportSans-Bold",
            fontSize=13, leading=18, spaceBefore=16, spaceAfter=9,
            textColor=colors.HexColor("#142c48"), keepWithNext=True,
        )
        title = ParagraphStyle("ReportTitle", parent=heading, fontSize=21, leading=27, spaceBefore=0, spaceAfter=18)
        story: list[Any] = [Paragraph("OSINT Toolkit<br/>Investigation Report", title)]

        def text(value: Any) -> str:
            value = "Not reported" if value is None else str(value)
            return escape(value).replace("\n", "<br/>")

        def paragraph(value: Any, label: str | None = None, depth: int = 0) -> None:
            style = ParagraphStyle(f"Depth{depth}", parent=body, leftIndent=min(depth, 4) * 12)
            content = f"<b>{text(label)}:</b> {text(value)}" if label else text(value)
            story.append(Paragraph(content, style))

        def render_value(value: Any, label: str | None = None, depth: int = 0) -> None:
            if isinstance(value, dict) and value:
                if label:
                    paragraph("", label, depth)
                for key, item in value.items():
                    render_value(item, str(key).replace("_", " ").title(), depth + (1 if label else 0))
            elif isinstance(value, (list, tuple)) and value:
                if all(not isinstance(item, (dict, list, tuple)) for item in value):
                    paragraph(", ".join(str(item) for item in value), label, depth)
                else:
                    if label:
                        paragraph("", label, depth)
                    for index, item in enumerate(value, 1):
                        render_value(item, f"Item {index}", depth + 1)
            else:
                paragraph("None returned" if value == [] or value == {} else value, label, depth)

        paragraph(report.report_id, "Report ID")
        paragraph(report.generated_at.isoformat(), "Generated")
        paragraph(", ".join(module.replace("_", " ") for module in report.requested_modules), "Modules requested")
        story.append(Paragraph("Target identifiers", heading))
        render_value(report.target.model_dump(exclude_none=True))
        for section in report.sections:
            if section.status == "not_requested":
                continue
            story.append(Paragraph(text(section.title), heading))
            paragraph(f"{section.status.replace('_', ' ').title()} - {section.summary}")
            if section.error_message:
                paragraph(section.error_message, "Provider note")
            if section.data:
                render_value(section.data)
        story.append(Paragraph("Findings summary", heading))
        for finding in report.findings:
            paragraph(finding)
        story.append(Spacer(1, 8))
        story.append(Paragraph("Limitations", heading))
        paragraph(report.limitations)

        def footer(canvas, document):
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#dbe2e9"))
            canvas.line(44, 34, A4[0] - 44, 34)
            canvas.setFont("ReportSans", 8)
            canvas.setFillColor(colors.HexColor("#5d6b7e"))
            canvas.drawString(44, 22, "OSINT Toolkit | Investigation report")
            canvas.drawRightString(A4[0] - 44, 22, f"Page {document.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return buffer.getvalue()
