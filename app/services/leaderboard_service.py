from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.user import UserRole, User
from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.commission_repository import CommissionRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse
from app.utils.date import parse_period


class LeaderboardService:

    @staticmethod
    async def get_leaderboard(
        organization_id: UUID,
        period: str,
        current_user: User,
        db: AsyncSession,
        limit: int = 10,
    ) -> LeaderboardResponse:
        # Validate period format
        try:
            parse_period(period)
        except ValueError:
            from app.core.exceptions import BadRequestException
            raise BadRequestException(
                "Invalid period format. Use YYYY-MM e.g. 2025-06"
            )

        org_repo = OrganizationRepository(db)
        org = await org_repo.get_by_id(organization_id)

        if not org:
            raise NotFoundException("Organization not found")

        # Staff cannot see leaderboard if org has disabled it
        if (
            current_user.role == UserRole.STAFF
            and not org.show_leaderboard
        ):
            raise ForbiddenException(
                "Leaderboard is not enabled for this organization"
            )

        commission_repo = CommissionRepository(db)
        rows = await commission_repo.get_leaderboard(
            organization_id, period, limit
        )

        is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPERADMIN)

        entries = []
        for i, row in enumerate(rows, start=1):
            entries.append(LeaderboardEntry(
                rank=i,
                staff_id=row["staff_id"],
                full_name=row["full_name"],
                # Only admins see email addresses
                email=row["email"] if is_admin else None,
                total_sales=row["total_sales"],
                total_revenue=row["total_revenue"],
                total_commission=row["total_commission"],
            ))

        return LeaderboardResponse(
            period=period,
            organization_name=org.name,
            commission_model=org.commission_model.value,
            entries=entries,
        )