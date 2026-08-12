"""FastAPI application factory, response safety, and request logging."""

import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import BreachRateLimitError, BreachUnavailableError, LookupNotFoundError, LookupTimeoutError, ShodanConfigurationError, ShodanRateLimitError, UpstreamLookupError
from app.core.logging import configure_logging, get_logger
from app.shared.schemas import error_envelope

logger = get_logger(__name__)


def _json_error(status: int, code: str, message: str, retry_after: int | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content=error_envelope(code, message, retry_after=retry_after).model_dump(mode="json", exclude_none=True))


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        started, status = time.perf_counter(), 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            if request.url.path.startswith("/api/v1"):
                parts = request.url.path.removeprefix("/api/v1/").split("/")
                logger.info("module=%s action=%s target=redacted status=%s duration_ms=%s", parts[0] if parts else "api", parts[1] if len(parts) > 1 else "root", status, round((time.perf_counter() - started) * 1000, 2))

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/docs", include_in_schema=False)
    def custom_swagger_docs() -> object:
        return get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{settings.app_name} API Reference")

    @app.exception_handler(UpstreamLookupError)
    async def upstream_error(_: Request, exc: UpstreamLookupError) -> JSONResponse:
        status, code, message = 502, "upstream_lookup_failed", "Lookup data is temporarily unavailable"
        if isinstance(exc, ShodanConfigurationError):
            status, code, message = 500, "provider_configuration_error", "This lookup provider is not configured"
        elif isinstance(exc, (ShodanRateLimitError, BreachRateLimitError)):
            status, code, message = 429, "rate_limit_exceeded", "Rate limit reached, try again later"
        elif isinstance(exc, BreachUnavailableError):
            status, code, message = 503, "provider_unavailable", "Breach data temporarily unavailable"
        elif isinstance(exc, LookupNotFoundError):
            status, code, message = 404, "not_found", "No data was found for this lookup"
        elif isinstance(exc, LookupTimeoutError):
            status, code, message = 504, "upstream_timeout", "The lookup timed out"
        logger.warning("module=core action=upstream_error target=redacted status=%s duration_ms=0", status, exc_info=True)
        return _json_error(status, code, message, getattr(exc, "retry_after", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        return _json_error(422, "validation_error", "Request input is invalid")

    @app.exception_handler(ValidationError)
    async def pydantic_validation_error(_: Request, __: ValidationError) -> JSONResponse:
        """Normalize validation raised while FastAPI constructs dependency models."""
        return _json_error(422, "validation_error", "Request input is invalid")

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return _json_error(exc.status_code, "http_error", "Requested resource was not found" if exc.status_code == 404 else "Request could not be completed")

    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, __: Exception) -> JSONResponse:
        logger.exception("module=core action=unhandled_exception target=redacted status=500 duration_ms=0")
        return _json_error(500, "internal_error", "An unexpected server error occurred")

    return app


app = create_app()
