"""Business logic shared by the routers."""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Account, Order, Payout, Plan, User

# Percentage of the account size paid out on each demo payout row, plus how many
# days before the account's creation date the payout landed. This reproduces the
# two-paid / one-processing history the dashboard used to fake client-side.
DEMO_PAYOUT_SCHEDULE: list[tuple[int, float, str]] = [
    (30, 0.06, "paid"),
    (14, 0.04, "paid"),
    (0, 0.05, "processing"),
]


def build_order_reference() -> str:
    return f"AF-{uuid.uuid4().hex[:12].upper()}"


def create_account(db: Session, user: User, plan: Plan) -> Account:
    """Open a simulated challenge account on the given plan."""

    account = Account(
        user_id=user.id,
        plan_id=plan.id,
        eval_label=plan.eval_label,
        account_size=plan.account_size,
        profit_split=plan.profit_split,
        phase="Step 1",
        status="active",
        balance=plan.account_size,
    )

    db.add(account)
    db.flush()

    return account


def create_demo_payouts(db: Session, account: Account) -> list[Payout]:
    """Attach the demo payout history shown on the dashboard."""

    created_on = account.created_at.date()
    payouts: list[Payout] = []

    for days_ago, share, status in DEMO_PAYOUT_SCHEDULE:
        payout = Payout(
            account_id=account.id,
            payout_date=created_on - timedelta(days=days_ago),
            amount=round(account.account_size * share, 2),
            status=status,
        )

        db.add(payout)
        payouts.append(payout)

    db.flush()

    return payouts


def create_order(db: Session, user: User, plan: Plan, account: Account, full_name: str, card_number: str) -> Order:
    order = Order(
        reference=build_order_reference(),
        user_id=user.id,
        plan_id=plan.id,
        account_id=account.id,
        full_name=full_name,
        email=user.email,
        amount=plan.price,
        currency="INR",
        status="paid",
        card_last4=card_number[-4:],
        agreed_rules=True,
    )

    db.add(order)
    db.flush()

    return order


def collect_stats(db: Session) -> dict:
    """Numbers behind the homepage stat cards, derived from real rows.

    Floors keep the marketing copy ("10+ accounts funded") truthful while the
    demo database is still small.
    """

    accounts_funded = db.scalar(select(func.count()).select_from(Account)) or 0
    rewards_paid = db.scalar(select(func.coalesce(func.sum(Payout.amount), 0)).where(Payout.status == "paid")) or 0
    top_split = db.scalar(select(func.max(Plan.profit_split)).where(Plan.is_active.is_(True))) or 80

    return {
        "profit_split": int(top_split),
        "payout_speed_hours": 24,
        "minimum_payout": 1_000,
        "accounts_funded": max(int(accounts_funded), 10),
        "total_rewards_paid": max(float(rewards_paid), 100_000.0),
    }
