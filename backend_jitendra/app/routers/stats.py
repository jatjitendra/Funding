"""Numbers behind the homepage stat cards."""

from __future__ import annotations

from fastapi import APIRouter

from ..deps import DbSession
from ..schemas import StatsOut
from ..services import collect_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats(db: DbSession) -> StatsOut:
    return StatsOut(**collect_stats(db))
