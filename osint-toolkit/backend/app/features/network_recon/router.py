"""HTTP routes for Shodan-backed network reconnaissance."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.network_recon.schemas import HostData, HostQuery, SearchData, SearchQuery
from app.features.network_recon.service import NetworkReconService
from app.shared.schemas import ResponseMeta, SuccessResponse
from app.shared.utils import utc_now


router = APIRouter(prefix="/network-recon", tags=["network-recon"])


def get_network_recon_service() -> NetworkReconService:
    """Provide the feature service; can be overridden in tests."""
    return NetworkReconService()


@router.get("/host", response_model=SuccessResponse[HostData])
def host_lookup(
    query: Annotated[HostQuery, Depends()],
    service: Annotated[NetworkReconService, Depends(get_network_recon_service)],
) -> SuccessResponse[HostData]:
    """Return Shodan intelligence for an IPv4 or IPv6 address."""
    return SuccessResponse(data=service.host(str(query.ip)), meta=ResponseMeta(queried_at=utc_now()))


@router.get("/search", response_model=SuccessResponse[SearchData])
def search_hosts(
    query: Annotated[SearchQuery, Depends()],
    service: Annotated[NetworkReconService, Depends(get_network_recon_service)],
) -> SuccessResponse[SearchData]:
    """Search Shodan and expose at most 20 hosts from the requested page."""
    return SuccessResponse(
        data=service.search(query.query.strip(), query.page),
        meta=ResponseMeta(queried_at=utc_now()),
    )
