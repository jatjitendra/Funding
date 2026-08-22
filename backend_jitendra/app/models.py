"""Database tables backing the ApexFund frontend."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Account.created_at",
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Plan(Base):
    """A challenge plan. Mirrors the PLANS array in js/data.js."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    eval_label: Mapped[str] = mapped_column(String(80), nullable=False)
    eval_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    account_size: Mapped[int] = mapped_column(Integer, nullable=False)
    original_price: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    profit_split: Mapped[int] = mapped_column(Integer, nullable=False)
    phase1_profit_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    phase2_profit_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    max_daily_loss_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    max_total_loss_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    most_popular: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    accounts: Mapped[list["Account"]] = relationship(back_populates="plan")


class Account(Base):
    """A simulated challenge account created by a completed checkout."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"), nullable=False)

    # Plan terms are copied onto the account so historical accounts keep the
    # pricing and rules they were sold under, even if the plan changes later.
    eval_label: Mapped[str] = mapped_column(String(80), nullable=False)
    account_size: Mapped[int] = mapped_column(Integer, nullable=False)
    profit_split: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str] = mapped_column(String(20), nullable=False, default="Step 1")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    user: Mapped[User] = relationship(back_populates="accounts")
    plan: Mapped[Plan] = relationship(back_populates="accounts")
    payouts: Mapped[list["Payout"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="Payout.payout_date",
    )
    order: Mapped["Order | None"] = relationship(back_populates="account", uselist=False)


class Order(Base):
    """A simulated purchase of a challenge plan.

    Only the last four digits of the card are kept; the full number, expiry and
    CVC are validated then discarded, since this is a demo with no real gateway.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"), nullable=False)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="paid")
    card_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    agreed_rules: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    user: Mapped[User] = relationship(back_populates="orders")
    account: Mapped[Account | None] = relationship(back_populates="order")


class Payout(Base):
    """Payout row shown in the dashboard's payout history table."""

    __tablename__ = "payouts"
    __table_args__ = (UniqueConstraint("account_id", "payout_date", name="uq_payout_account_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    payout_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    account: Mapped[Account] = relationship(back_populates="payouts")


class ContactMessage(Base):
    """Submission from the "Need help? Contact us" form on the homepage."""

    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    mobile: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_handled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
