from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    field_errors: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
    request_id: str


class PageMeta(BaseModel):
    next_cursor: str | None = None
    has_next: bool = False


class DataResponse(BaseModel, Generic[T]):
    data: T
    request_id: str


class ListResponse(BaseModel, Generic[T]):
    data: list[T]
    page: PageMeta = Field(default_factory=PageMeta)
    request_id: str
