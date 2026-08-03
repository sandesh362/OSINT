"""HTTP routes for the domain intelligence feature."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.domain_intel.schemas import DnsData, DomainQuery, WhoisData
from app.features.domain_intel.service import DomainIntelService
from app.shared.schemas import ResponseMeta, SuccessResponse
from app.shared.utils import utc_now


router = APIRouter(prefix="/domain-intel", tags=["domain-intel"])


def get_domain_intel_service() -> DomainIntelService:
    """Provide a service instance; overridden by tests or future DI wiring."""
    return DomainIntelService()


@router.get("/whois", response_model=SuccessResponse[WhoisData])
def whois_lookup(
    query: Annotated[DomainQuery, Depends()],
    service: Annotated[DomainIntelService, Depends(get_domain_intel_service)],
) -> SuccessResponse[WhoisData]:
    """Fetch public WHOIS registration information for a domain."""
    return SuccessResponse(data=service.whois(query.domain), meta=ResponseMeta(queried_at=utc_now()))


@router.get("/dns", response_model=SuccessResponse[DnsData])
def dns_lookup(
    query: Annotated[DomainQuery, Depends()],
    service: Annotated[DomainIntelService, Depends(get_domain_intel_service)],
) -> SuccessResponse[DnsData]:
    """Fetch selected DNS record types for a domain."""
    return SuccessResponse(data=service.dns(query.domain), meta=ResponseMeta(queried_at=utc_now()))
