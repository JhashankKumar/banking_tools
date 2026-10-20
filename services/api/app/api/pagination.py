from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query

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
