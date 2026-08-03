"""Common response envelope models."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    """Metadata included with successful feature responses."""

    queried_at: datetime


class SuccessResponse(BaseModel, Generic[DataT]):
    """Consistent success envelope for all feature APIs."""

    success: bool = True
    data: DataT
    meta: ResponseMeta


class ErrorDetail(BaseModel):
    """Machine-readable application error body."""

    success: bool = False
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now().astimezone())
