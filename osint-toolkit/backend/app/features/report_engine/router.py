"""HTTP generation and one-time preview routes for investigation reports."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.features.report_engine.generators.html_generator import HtmlReportGenerator
from app.features.report_engine.generators.pdf_generator import PdfReportGenerator
from app.features.report_engine.schemas import HtmlReportData, PreviewData, ReportRequest
from app.features.report_engine.service import ReportEngineService
from app.shared.schemas import ResponseMeta, SuccessResponse
from app.shared.utils import utc_now


router = APIRouter(prefix="/report-engine", tags=["report-engine"])


def get_report_engine_service() -> ReportEngineService:
    return ReportEngineService()


def get_html_generator() -> HtmlReportGenerator:
    return HtmlReportGenerator()


def get_pdf_generator() -> PdfReportGenerator:
    return PdfReportGenerator()


@router.post("/generate", response_model=SuccessResponse[HtmlReportData])
async def generate_report(
    request: ReportRequest,
    service: Annotated[ReportEngineService, Depends(get_report_engine_service)],
    html_generator: Annotated[HtmlReportGenerator, Depends(get_html_generator)],
    pdf_generator: Annotated[PdfReportGenerator, Depends(get_pdf_generator)],
) -> SuccessResponse[HtmlReportData] | Response:
    report = await service.generate(request)
    html = html_generator.render(report)
    service.cache_report(report, html)
    if request.format == "pdf":
        pdf = pdf_generator.render(html)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="osint-report-{report.report_id}.pdf"'},
        )
    return SuccessResponse(data=HtmlReportData(report_id=report.report_id, html=html), meta=ResponseMeta(queried_at=utc_now()))


@router.get("/preview/{report_id}", response_model=SuccessResponse[PreviewData])
async def preview_report(
    report_id: str,
    service: Annotated[ReportEngineService, Depends(get_report_engine_service)],
) -> SuccessResponse[PreviewData]:
    cached = service.take_preview(report_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="Report preview is unavailable or has expired")
    return SuccessResponse(data=PreviewData(report_id=report_id, html=cached.html), meta=ResponseMeta(queried_at=utc_now()))
