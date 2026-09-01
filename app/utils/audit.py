from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository


async def log_action(
    db: AsyncSession,
    organization_id: UUID,
    action: str,
    resource_type: str,
    actor: User = None,
    resource_id=None,
    metadata: dict = None,
) -> None:
    """
    Write an audit log entry. Always call this before db.commit()
    so the log and the action are committed atomically
    either both save or neither does.
    """
    repo = AuditLogRepository(db)
    await repo.create(
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        actor=actor,
        resource_id=resource_id,
        metadata=metadata,
    )