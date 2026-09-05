from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_staff
from app.models.user import User
from app.schemas.leaderboard import LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter()


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    period: str = Query(..., description="Period in YYYY-MM format e.g. 2025-06"),
    limit: int = Query(10, ge=1, le=50, description="Number of entries to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_staff),
):
 
    return await LeaderboardService.get_leaderboard(
        organization_id=current_user.organization_id,
        period=period,
        current_user=current_user,
        db=db,
        limit=limit,
    )