from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
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
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.organization import OrganizationCreate
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository


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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An organization with this email already exists",
            )

        if await user_repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )

        # Generate unique slug
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
        user_repo = UserRepository(db)
        org_repo = OrganizationRepository(db)

        user = await user_repo.get_by_email(payload.email)

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated",
            )

        org = await org_repo.get_by_id(user.organization_id)
        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is inactive or does not exist",
            )

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

        if token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user = await user_repo.get_by_id(token_data["sub"])

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

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