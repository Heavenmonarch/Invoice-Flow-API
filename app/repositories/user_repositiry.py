from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.models.user import User, UserRole
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_org(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: UUID,
        page: int = 1,
        per_page: int = 20,
        role: UserRole = None,
        active_only: bool = True,
    ) -> tuple[list[User], int]:
        query = select(User).where(User.organization_id == organization_id)

        if active_only:
            query = query.where(User.is_active == True)
        if role:
            query = query.where(User.role == role)

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self.db.execute(
            query.order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return result.scalars().all(), total

    async def email_taken(self, email: str, exclude_id: UUID = None) -> bool:
        query = select(User).where(User.email == email)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def count_by_org(self, organization_id: UUID) -> int:
        return await self.db.scalar(
            select(func.count(User.id)).where(
                User.organization_id == organization_id,
                User.is_active == True,
            )
        )