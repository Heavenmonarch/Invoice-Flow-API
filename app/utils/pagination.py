from app.schemas.common import PaginatedResponse
from typing import TypeVar, List

T = TypeVar("T")


def paginate (items: List[T], total: int, page: int, per_page:int) -> PaginatedResponse:
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=-(-total // per_page),
    )