from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import io

from app.core.exceptions import BadRequestException, NotFoundException
from app.repositories.commission_repository import CommissionRepository
from app.repositories.organization_repository import OrganizationRepository
from app.utils.export import generate_commission_csv, generate_commission_pdf
from app.utils.date import parse_period


class ExportService:

    @staticmethod
    async def export_commissions(
        organization_id: UUID,
        period: str,
        format: str,
        db: AsyncSession,
    ) -> tuple[io.BytesIO | io.StringIO, str, str]:
        """
        Returns a tuple of (buffer, filename, media_type).
        The endpoint streams this directly to the client.
        """
        # Validate period format
        try:
            parse_period(period)
        except ValueError:
            raise BadRequestException(
                "Invalid period format. Use YYYY-MM e.g. 2025-06"
            )

        # Validate format
        if format not in ("csv", "pdf"):
            raise BadRequestException("Format must be 'csv' or 'pdf'")

        # Fetch org for name
        org_repo = OrganizationRepository(db)
        org = await org_repo.get_by_id(organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Fetch data
        commission_repo = CommissionRepository(db)
        rows = await commission_repo.get_export_data(organization_id, period)

        if not rows:
            raise BadRequestException(
                f"No commission data found for period {period}"
            )

        org_slug = org.slug.replace("-", "_")
        filename = f"commissions_{org_slug}_{period}"

        if format == "csv":
            buffer = generate_commission_csv(rows, period, org.name)
            return buffer, f"{filename}.csv", "text/csv"
        else:
            buffer = generate_commission_pdf(rows, period, org.name)
            return buffer, f"{filename}.pdf", "application/pdf"