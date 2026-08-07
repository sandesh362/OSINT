"""HTTP routes for provider-backed, minimal breach exposure summaries."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.breach_check.schemas import BreachCheckData, EmailQuery
from app.features.breach_check.service import BreachCheckService
from app.shared.schemas import ResponseMeta, SuccessResponse
from app.shared.utils import utc_now


router = APIRouter(prefix="/breach-check", tags=["breach-check"])


def get_breach_check_service() -> BreachCheckService:
    """Provide the feature service; tests can replace this dependency."""
    return BreachCheckService()


@router.get("/email", response_model=SuccessResponse[BreachCheckData])
async def email_lookup(
    query: Annotated[EmailQuery, Depends()],
    service: Annotated[BreachCheckService, Depends(get_breach_check_service)],
) -> SuccessResponse[BreachCheckData]:
    """Report only breach metadata for a supplied email address."""
    return SuccessResponse(data=await service.email(query.value), meta=ResponseMeta(queried_at=utc_now()))
