from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import secrets
import string

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.core.security import hash_password
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
)
from app.schemas.user import StaffInvite, UserUpdate
from app.schemas.common import PaginatedResponse
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.utils.pagination import paginate
from app.utils.email import send_staff_invitation
from app.utils.audit import log_action


def _generate_temp_password(length: int = 12) -> str:

    # Generates a secure random password that meets common requirements: at least one uppercase, one lowercase, one digit, one symbol.
   
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*" for c in password)
        ):
            return password


class UserService:

    @staticmethod
    async def invite_staff(
        payload: StaffInvite,
        organization_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> User:
        user_repo = UserRepository(db)
        org_repo = OrganizationRepository(db)

        if payload.role == UserRole.SUPERADMIN:
            raise BadRequestException("Superadmin role cannot be assigned manually")

        if await user_repo.email_taken(payload.email):
            raise ConflictException("A user with this email already exists")

        # Fetch org name for the email
        org = await org_repo.get_by_id(organization_id)

        # Generate a secure temporary password
        temp_password = _generate_temp_password()

        user = User(
            organization_id=organization_id,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(temp_password),
            role=payload.role,
            is_active=True,
        )
        user = await user_repo.create(user)

        # Log before commit. atomic with the user creation
        await log_action(
            db=db,
            organization_id=organization_id,
            action="user.invited",
            resource_type="user",
            actor=current_user,
            resource_id=user.id,
            metadata={
                "invited_email": payload.email,
                "invited_role": payload.role.value,
            },
        )

        await db.commit()
        await db.refresh(user)

        # Send email AFTER commit. if email fails, user is still created
        send_staff_invitation(
            to=payload.email,
            full_name=payload.full_name,
            organization_name=org.name if org else "Your Organization",
            temp_password=temp_password,
        )

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
        current_user: User,
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

        old_values = {k: getattr(user, k) for k in updates}

        for field, value in updates.items():
            setattr(user, field, value)

        await log_action(
            db=db,
            organization_id=organization_id,
            action="user.updated",
            resource_type="user",
            actor=current_user,
            resource_id=user_id,
            metadata={"changes": updates, "previous": old_values},
        )

        return await user_repo.save(user)

    @staticmethod
    async def deactivate_user(
        user_id: UUID,
        organization_id: UUID,
        current_user: User,
        db: AsyncSession,
    ) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id_and_org(user_id, organization_id)

        if not user:
            raise NotFoundException("User not found")

        if user.role == UserRole.SUPERADMIN:
            raise BadRequestException("Superadmin account cannot be deactivated")

        user.is_active = False

        await log_action(
            db=db,
            organization_id=organization_id,
            action="user.deactivated",
            resource_type="user",
            actor=current_user,
            resource_id=user_id,
            metadata={"deactivated_email": user.email},
        )

        return await user_repo.save(user)