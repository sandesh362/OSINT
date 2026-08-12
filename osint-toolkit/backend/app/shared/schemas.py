"""Shared API envelopes used by every JSON endpoint and error handler."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    """Timestamp assigned when the application completes a response."""

    queried_at: datetime


class ErrorInfo(BaseModel):
    """Safe, client-facing error information; internal details stay in logs."""

    code: str
    message: str
    retry_after: int | None = None


class SuccessResponse(BaseModel, Generic[DataT]):
    """Consistent successful JSON response envelope."""

    success: bool = True
    data: DataT
    meta: ResponseMeta
    error: None = None


class ErrorResponse(BaseModel):
    """Consistent failed JSON response envelope."""

    success: bool = False
    data: None = None
    meta: ResponseMeta
    error: ErrorInfo


def error_envelope(code: str, message: str, *, retry_after: int | None = None) -> ErrorResponse:
    """Build a safe error response without exposing provider internals."""
    return ErrorResponse(
        meta=ResponseMeta(queried_at=datetime.now().astimezone()),
        error=ErrorInfo(code=code, message=message, retry_after=retry_after),
    )
