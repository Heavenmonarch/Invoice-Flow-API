from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        organization_id: UUID,
        action: str,
        resource_type: str,
        actor: User = None,
        resource_id: str = None,
        metadata: dict = None,
    ) -> AuditLog:
        log = AuditLog(
            organization_id=organization_id,
            actor_id=actor.id if actor else None,
            actor_email=actor.email if actor else "system",
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            metadata=metadata or {},
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_by_org(
        self,
        organization_id: UUID,
        resource_type: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).where(
            AuditLog.organization_id == organization_id
        )

        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total