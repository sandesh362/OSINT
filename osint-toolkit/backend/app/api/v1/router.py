"""Aggregate feature routers for API v1."""

from fastapi import APIRouter

from app.features.breach_check.router import router as breach_check_router
from app.features.domain_intel.router import router as domain_intel_router
from app.features.network_recon.router import router as network_recon_router
from app.features.social_profiling.router import router as social_profiling_router


api_router = APIRouter()
api_router.include_router(domain_intel_router)
api_router.include_router(network_recon_router)
api_router.include_router(social_profiling_router)
api_router.include_router(breach_check_router)

# Future features are added here with one include_router call each.
