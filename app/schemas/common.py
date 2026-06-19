from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse (BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    
class MessageResponse(BaseModel):
    message: str
    
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    
class DeleteResponse(BaseModel):
    message: str
    code: int