"""The signed-in trader's simulated accounts and payout history.

Backs dashboard.js, which previously read from localStorage.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..deps import CurrentUser, DbSession
from ..models import Account, Payout, User
from ..schemas import AccountOut, PayoutOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _get_owned_account(db: Session, user: User, account_id: int) -> Account:
    account = db.scalar(
        select(Account)
        .options(joinedload(Account.user))
        .where(Account.id == account_id, Account.user_id == user.id)
    )

    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    return account


@router.get("", response_model=list[AccountOut])
def list_my_accounts(current_user: CurrentUser, db: DbSession) -> list[AccountOut]:
    accounts = db.scalars(
        select(Account)
        .options(joinedload(Account.user))
        .where(Account.user_id == current_user.id)
        .order_by(Account.created_at)
    )

    return [AccountOut.from_model(account) for account in accounts]


@router.get("/latest", response_model=AccountOut)
def get_latest_account(current_user: CurrentUser, db: DbSession) -> AccountOut:
    """The dashboard shows the most recently opened account."""

    account = db.scalar(
        select(Account)
        .options(joinedload(Account.user))
        .where(Account.user_id == current_user.id)
        .order_by(Account.created_at.desc(), Account.id.desc())
        .limit(1)
    )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No challenge accounts yet. Buy a challenge to see your simulated account here.",
        )

    return AccountOut.from_model(account)


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, current_user: CurrentUser, db: DbSession) -> AccountOut:
    return AccountOut.from_model(_get_owned_account(db, current_user, account_id))


@router.get("/{account_id}/payouts", response_model=list[PayoutOut])
def list_account_payouts(account_id: int, current_user: CurrentUser, db: DbSession) -> list[PayoutOut]:
    _get_owned_account(db, current_user, account_id)

    payouts = db.scalars(
        select(Payout).where(Payout.account_id == account_id).order_by(Payout.payout_date, Payout.id)
    )

    return [PayoutOut.from_model(payout) for payout in payouts]
