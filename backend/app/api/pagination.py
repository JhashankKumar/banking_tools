from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

MAX_LIMIT = 100


@dataclass(frozen=True)
class PageParams:
    limit: int
    offset: int


def page_params(
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


Page = Annotated[PageParams, Depends(page_params)]


def count_rows(session: Session, query: Select[*tuple[Any, ...]]) -> int:
    """Total rows the query would return before paging (the `page.total` of a list response)."""
    return session.scalar(select(func.count()).select_from(query.subquery())) or 0


def paged[*Ts](query: Select[*Ts], page: PageParams) -> Select[*Ts]:
    """The query limited to one page. Callers order the query first so pages are stable."""
    return query.limit(page.limit).offset(page.offset)
