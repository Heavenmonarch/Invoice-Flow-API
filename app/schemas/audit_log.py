import uuid
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLogOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    actor_id: Optional[uuid.UUID]
    actor_email: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}