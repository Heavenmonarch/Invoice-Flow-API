from sqlalchemy.ext.asyncio import AsyncSession
import re

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.utils.lockout import (
    is_locked_out,
    record_failed_attempt,
    clear_failed_attempts,
    get_remaining_attempts,
    get_lockout_ttl,
    LOCKOUT_WINDOW_SECONDS,
)
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ForbiddenException,
    AppException,
)
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.organization import OrganizationCreate
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.utils.lockout import (
    is_locked_out,
    record_failed_attempt,
    clear_failed_attempts,
    get_remaining_attempts,
    get_lockout_ttl,
)
from fastapi import status


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class AuthService:

    @staticmethod
    async def register(
        payload: OrganizationCreate,
        db: AsyncSession,
    ) -> Organization:
        org_repo = OrganizationRepository(db)
        user_repo = UserRepository(db)

        if await org_repo.get_by_email(payload.email):
            raise ConflictException("An organization with this email already exists")

        if await user_repo.get_by_email(payload.email):
            raise ConflictException("Email already in use")

        base_slug = slugify(payload.name)
        slug = base_slug
        counter = 1
        while await org_repo.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            name=payload.name,
            slug=slug,
            email=payload.email,
            is_active=True,
        )
        org = await org_repo.create(org)

        superadmin = User(
            organization_id=org.id,
            email=payload.email,
            full_name=payload.name,
            hashed_password=hash_password(payload.password),
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        await user_repo.create(superadmin)
        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def login(
        payload: LoginRequest,
        db: AsyncSession,
    ) -> TokenResponse:
        org_repo = OrganizationRepository(db)
        user_repo = UserRepository(db)

        if await is_locked_out(payload.email):
            ttl = await get_lockout_ttl(payload.email)
            minutes = ttl // 60
            seconds = ttl % 60
            raise AppException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Account temporarily locked due to too many failed attempts. "
                    f"Try again in {minutes}m {seconds}s."
                ),
                code="ACCOUNT_LOCKED",
            )

       
        user = await user_repo.get_by_email(payload.email)

       
        if not user or not verify_password(payload.password, user.hashed_password):
            # Record the failure regardless of whether email exists
            # This prevents email enumeration via timing differences
            await record_failed_attempt(payload.email)
            remaining = await get_remaining_attempts(payload.email)

            if remaining == 0:
                raise AppException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        "Too many failed attempts. "
                        f"Account locked for {LOCKOUT_WINDOW_SECONDS // 60} minutes."
                    ),
                    code="ACCOUNT_LOCKED",
                )

            raise UnauthorizedException(
                f"Invalid email or password. "
                f"{remaining} attempt{'s' if remaining != 1 else ''} remaining."
            )

     
        if not user.is_active:
            raise ForbiddenException("This account has been deactivated")

        org = await org_repo.get_by_id(user.organization_id)
        if not org or not org.is_active:
            raise ForbiddenException("Organization is inactive or does not exist")

    
        await clear_failed_attempts(payload.email)

        access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "role": user.role.value,
                "org_id": str(user.organization_id),
            },
        )
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    async def refresh(
        payload: RefreshRequest,
        db: AsyncSession,
    ) -> TokenResponse:
        user_repo = UserRepository(db)

        try:
            token_data = decode_token(payload.refresh_token)
        except ValueError as e:
            raise UnauthorizedException(str(e))

        if token_data.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        user = await user_repo.get_by_id(token_data["sub"])

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "role": user.role.value,
                "org_id": str(user.organization_id),
            },
        )
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )