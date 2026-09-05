from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/commissions")
async def export_commissions(
    period: str = Query(..., description="Period in YYYY-MM format e.g. 2025-06"),
    format: str = Query("pdf", description="Export format: 'pdf' or 'csv'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Download commission report for a period as PDF or CSV.
    Only accessible by admins and superadmins.
    """
    buffer, filename, media_type = await ExportService.export_commissions(
        organization_id=current_user.organization_id,
        period=period,
        format=format,
        db=db,
    )

    return StreamingResponse(
        content=buffer,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-store",
        },
    )