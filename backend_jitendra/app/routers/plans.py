"""Challenge plan catalogue, replacing the PLANS array in js/data.js."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import DbSession
from ..models import Plan
from ..schemas import PlanOut

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanOut])
def list_plans(db: DbSession, include_inactive: bool = False) -> list[Plan]:
    query = select(Plan).order_by(Plan.sort_order, Plan.account_size)

    if not include_inactive:
        query = query.where(Plan.is_active.is_(True))

    return list(db.scalars(query))


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str, db: DbSession) -> Plan:
    plan = db.get(Plan, plan_id)

    if plan is None or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found. Pick a challenge from the pricing page to continue.",
        )

    return plan
