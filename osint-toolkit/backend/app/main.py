"""FastAPI application factory and exception-handler wiring."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    LookupNotFoundError,
    LookupProviderError,
    LookupTimeoutError,
    ShodanConfigurationError,
    ShodanRateLimitError,
    UpstreamLookupError,
)
from app.core.logging import configure_logging
from app.shared.schemas import ErrorDetail


def create_app() -> FastAPI:
    """Create the configured API application."""
    settings = get_settings()
    configure_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(UpstreamLookupError)
    async def upstream_lookup_exception_handler(_: Request, exc: UpstreamLookupError) -> JSONResponse:
        status_code = 502
        error = "upstream_lookup_failed"
        if isinstance(exc, ShodanConfigurationError):
            status_code, error = 500, "provider_configuration_error"
        elif isinstance(exc, ShodanRateLimitError):
            status_code, error = 429, "rate_limit_exceeded"
        elif isinstance(exc, LookupNotFoundError):
            status_code, error = 404, "not_found"
        elif isinstance(exc, LookupTimeoutError):
            status_code, error = 504, "upstream_timeout"
        elif isinstance(exc, LookupProviderError):
            status_code, error = 502, "upstream_lookup_failed"
        body = ErrorDetail(error=error, detail=exc.message).model_dump(mode="json")
        return JSONResponse(status_code=status_code, content=body)

    return app


app = create_app()
