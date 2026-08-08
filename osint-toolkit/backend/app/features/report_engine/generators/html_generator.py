"""Jinja2 renderer for normalized investigation reports."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.features.report_engine.schemas import InvestigationReport


TEMPLATE_DIRECTORY = Path(__file__).resolve().parent.parent / "templates"


class HtmlReportGenerator:
    """Render reports without knowing any upstream feature schema."""

    def __init__(self) -> None:
        self.environment = Environment(
            loader=FileSystemLoader(TEMPLATE_DIRECTORY),
            autoescape=select_autoescape(["html", "j2"]),
        )

    def render(self, report: InvestigationReport) -> str:
        return self.environment.get_template("report.html.j2").render(report=report)
