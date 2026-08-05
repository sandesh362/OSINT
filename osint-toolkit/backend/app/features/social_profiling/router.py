"""HTTP routes for conservative public social-profile discovery."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.social_profiling.schemas import UsernameLookupData, UsernameQuery
from app.features.social_profiling.service import SocialProfilingService
from app.shared.schemas import ResponseMeta, SuccessResponse
from app.shared.utils import utc_now


router = APIRouter(prefix="/social-profiling", tags=["social-profiling"])


def get_social_profiling_service() -> SocialProfilingService:
    """Provide the feature service; tests can replace this dependency."""
    return SocialProfilingService()


@router.get("/username", response_model=SuccessResponse[UsernameLookupData])
async def username_lookup(
    query: Annotated[UsernameQuery, Depends()],
    service: Annotated[SocialProfilingService, Depends(get_social_profiling_service)],
) -> SuccessResponse[UsernameLookupData]:
    """Check configured public profile URLs for an exact username only."""
    return SuccessResponse(data=await service.username(query.value), meta=ResponseMeta(queried_at=utc_now()))
