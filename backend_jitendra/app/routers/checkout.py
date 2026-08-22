"""Simulated checkout: validates the card, records an order, opens an account.

No payment gateway is contacted and no card data is persisted beyond the last
four digits, matching the demo banner on checkout.html.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import CurrentUser, DbSession
from ..models import Order, Plan
from ..schemas import AccountOut, CheckoutRequest, CheckoutResponse, OrderOut, PayoutOut
from ..services import create_account, create_demo_payouts, create_order

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def submit_checkout(payload: CheckoutRequest, current_user: CurrentUser, db: DbSession) -> CheckoutResponse:
    plan = db.get(Plan, payload.plan_id)

    if plan is None or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found. Pick a challenge from the pricing page to continue.",
        )

    account = create_account(db, current_user, plan)
    payouts = create_demo_payouts(db, account)
    order = create_order(
        db,
        user=current_user,
        plan=plan,
        account=account,
        full_name=payload.full_name.strip(),
        card_number=payload.card_number,
    )

    db.commit()
    db.refresh(account)
    db.refresh(order)

    return CheckoutResponse(
        order=OrderOut.model_validate(order),
        account=AccountOut.from_model(account),
        payouts=[PayoutOut.from_model(payout) for payout in payouts],
    )


@router.get("/orders", response_model=list[OrderOut])
def list_my_orders(current_user: CurrentUser, db: DbSession) -> list[Order]:
    return list(
        db.scalars(
            select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc(), Order.id.desc())
        )
    )
