from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.user import User, UserRole
from app.core.security import hash_password
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
)
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.common import PaginatedResponse
from app.repositories.user_repository import UserRepository
from app.utils.pagination import paginate


class UserService:

    @staticmethod
    async def create_user(
        payload: UserCreate,
        organization_id: UUID,
        db: AsyncSession,
    ) -> User:
        user_repo = UserRepository(db)

        if payload.role == UserRole.SUPERADMIN:
            raise BadRequestException("Superadmin role cannot be assigned manually")

        if await user_repo.email_taken(payload.email):
            raise ConflictException("A user with this email already exists")

        user = User(
            organization_id=organization_id,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=payload.role,
            is_active=True,
        )
        user = await user_repo.create(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def list_users(
        db: AsyncSession,
        organization_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        user_repo = UserRepository(db)
        users, total = await user_repo.list_by_org(
            organization_id, page, per_page
        )
        return paginate(users, total, page, per_page)

    @staticmethod
    async def get_user(
        user_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
    ) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id_and_org(user_id, organization_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    @staticmethod
    async def update_user(
        user_id: UUID,
        payload: UserUpdate,
        organization_id: UUID,
        db: AsyncSession,
    ) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id_and_org(user_id, organization_id)

        if not user:
            raise NotFoundException("User not found")

        if user.role == UserRole.SUPERADMIN:
            raise BadRequestException("Superadmin account cannot be modified")

        updates = payload.model_dump(exclude_unset=True)

        if "email" in updates:
            if await user_repo.email_taken(updates["email"], exclude_id=user_id):
                raise ConflictException("Email already in use")

        for field, value in updates.items():
            setattr(user, field, value)

        return await user_repo.save(user)

    @staticmethod
    async def deactivate_user(
        user_id: UUID,
        organization_id: UUID,
        db: AsyncSession,
    ) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id_and_org(user_id, organization_id)

        if not user:
            raise NotFoundException("User not found")

        if user.role == UserRole.SUPERADMIN:
            raise BadRequestException("Superadmin account cannot be deactivated")

        user.is_active = False
        return await user_repo.save(user)