"""Success envelopes (docs/project/API_AND_CODE_CONVENTIONS.md §1.1)."""

from collections.abc import Sequence

from pydantic import BaseModel

from app.api.pagination import PageParams


class DataResponse[T](BaseModel):
    data: T


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class PageResponse[T](BaseModel):
    data: list[T]
    page: PageMeta


def page_of[T](items: Sequence[T], total: int, params: PageParams) -> PageResponse[T]:
    return PageResponse[T](
        data=list(items), page=PageMeta(total=total, limit=params.limit, offset=params.offset)
    )
