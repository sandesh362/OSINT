"""FastAPI application factory and exception-handler wiring."""

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    BreachConfigurationError,
    BreachRateLimitError,
    BreachUnavailableError,
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
    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/docs", include_in_schema=False)
    def custom_swagger_docs() -> object:
        """Serve Swagger UI with lightweight project branding for lab use."""
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} API Reference",
            swagger_ui_parameters={"docExpansion": "list", "defaultModelsExpandDepth": 1},
        )
        style = """<style>
        body { background: #f4f7fb; } .swagger-ui .topbar { background: #11396d; }
        .swagger-ui .topbar .download-url-wrapper { display: none; }
        .swagger-ui .info .title { color: #11396d; } .swagger-ui .scheme-container { box-shadow: none; }
        .swagger-ui .opblock.opblock-get { border-color: #3976b9; background: #eef6ff; }
        .swagger-ui .btn.authorize { border-color: #153e75; color: #153e75; }
        </style>"""
        return type(response)(content=response.body.decode("utf-8").replace("</head>", f"{style}</head>"), media_type="text/html")

    @app.exception_handler(UpstreamLookupError)
    async def upstream_lookup_exception_handler(_: Request, exc: UpstreamLookupError) -> JSONResponse:
        status_code = 502
        error = "upstream_lookup_failed"
        if isinstance(exc, (ShodanConfigurationError, BreachConfigurationError)):
            status_code, error = 500, "provider_configuration_error"
        elif isinstance(exc, (ShodanRateLimitError, BreachRateLimitError)):
            status_code, error = 429, "rate_limit_exceeded"
        elif isinstance(exc, BreachUnavailableError):
            status_code, error = 503, "provider_unavailable"
        elif isinstance(exc, LookupNotFoundError):
            status_code, error = 404, "not_found"
        elif isinstance(exc, LookupTimeoutError):
            status_code, error = 504, "upstream_timeout"
        elif isinstance(exc, LookupProviderError):
            status_code, error = 502, "upstream_lookup_failed"
        retry_after = exc.retry_after if isinstance(exc, BreachRateLimitError) else None
        body = ErrorDetail(error=error, detail=exc.message, retry_after=retry_after).model_dump(mode="json", exclude_none=True)
        return JSONResponse(status_code=status_code, content=body)

    return app


app = create_app()
