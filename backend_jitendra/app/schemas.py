"""Request and response models.

Field names are snake_case in Python but serialised as camelCase, so the JSON
matches the keys the existing frontend JavaScript already reads (accountSize,
profitSplit, planId, evalLabel, ...). Requests accept either spelling.
"""

from __future__ import annotations

import re
from datetime import date as date_type
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from . import models


def to_camel(value: str) -> str:
    head, *rest = value.split("_")

    return head + "".join(part[:1].upper() + part[1:] for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #

Password = Annotated[str, Field(min_length=6, max_length=128)]


class SignupRequest(ApiModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    email: EmailStr
    password: Password

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Please enter your full name.")

        return cleaned


class LoginRequest(ApiModel):
    email: EmailStr
    password: str


class UserOut(ApiModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class TokenResponse(ApiModel):
    token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


# --------------------------------------------------------------------------- #
# Plans
# --------------------------------------------------------------------------- #


class PlanOut(ApiModel):
    id: str
    eval_label: str
    eval_steps: int
    account_size: int
    original_price: int
    price: int
    profit_split: int
    phase1_profit_pct: int
    phase2_profit_pct: int
    max_daily_loss_pct: int
    max_total_loss_pct: int
    most_popular: bool


# --------------------------------------------------------------------------- #
# Accounts and payouts
# --------------------------------------------------------------------------- #


class AccountOut(ApiModel):
    id: int
    plan_id: str
    email: EmailStr
    eval_label: str
    account_size: int
    profit_split: int
    phase: str
    status: str
    balance: float
    created_at: datetime

    @classmethod
    def from_model(cls, account: models.Account) -> "AccountOut":
        return cls(
            id=account.id,
            plan_id=account.plan_id,
            email=account.user.email,
            eval_label=account.eval_label,
            account_size=account.account_size,
            profit_split=account.profit_split,
            phase=account.phase,
            status=account.status,
            balance=float(account.balance),
            created_at=account.created_at,
        )


class PayoutOut(ApiModel):
    id: int
    account_id: int
    date: date_type
    amount: float
    status: str

    @classmethod
    def from_model(cls, payout: models.Payout) -> "PayoutOut":
        return cls(
            id=payout.id,
            account_id=payout.account_id,
            date=payout.payout_date,
            amount=float(payout.amount),
            status=payout.status,
        )


# --------------------------------------------------------------------------- #
# Checkout
# --------------------------------------------------------------------------- #

_EXPIRY_PATTERN = re.compile(r"^(0[1-9]|1[0-2])\s*/\s*([0-9]{2})$")


class CheckoutRequest(ApiModel):
    plan_id: Annotated[str, Field(min_length=1, max_length=60)]
    full_name: Annotated[str, Field(min_length=1, max_length=120)]
    agree_rules: bool
    card_name: Annotated[str, Field(min_length=1, max_length=120)]
    card_number: Annotated[str, Field(min_length=12, max_length=25)]
    card_expiry: str
    card_cvc: str

    @field_validator("agree_rules")
    @classmethod
    def must_agree(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must confirm you have read the Phase 1 and Phase 2 rules.")

        return value

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, value: str) -> str:
        digits = re.sub(r"[\s-]", "", value)

        if not digits.isdigit() or not 13 <= len(digits) <= 19:
            raise ValueError("Enter a valid card number.")

        if not _passes_luhn(digits):
            raise ValueError("That card number is not valid.")

        return digits

    @field_validator("card_expiry")
    @classmethod
    def validate_expiry(cls, value: str) -> str:
        match = _EXPIRY_PATTERN.match(value.strip())

        if not match:
            raise ValueError("Enter the expiry as MM/YY.")

        month, short_year = int(match.group(1)), int(match.group(2))
        today = date_type.today()
        expiry_year = 2000 + short_year

        # A card is valid through the last day of its expiry month.
        if (expiry_year, month) < (today.year, today.month):
            raise ValueError("That card has expired.")

        return f"{month:02d}/{short_year:02d}"

    @field_validator("card_cvc")
    @classmethod
    def validate_cvc(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned.isdigit() or not 3 <= len(cleaned) <= 4:
            raise ValueError("Enter a valid 3 or 4 digit CVC.")

        return cleaned


def _passes_luhn(digits: str) -> bool:
    total = 0

    for index, char in enumerate(reversed(digits)):
        digit = int(char)

        if index % 2 == 1:
            digit *= 2

            if digit > 9:
                digit -= 9

        total += digit

    return total % 10 == 0


class OrderOut(ApiModel):
    id: int
    reference: str
    plan_id: str
    account_id: int | None
    full_name: str
    email: EmailStr
    amount: float
    currency: str
    status: str
    card_last4: str
    created_at: datetime


class CheckoutResponse(ApiModel):
    order: OrderOut
    account: AccountOut
    payouts: list[PayoutOut]


# --------------------------------------------------------------------------- #
# Contact
# --------------------------------------------------------------------------- #


class ContactRequest(ApiModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    mobile: Annotated[str, Field(min_length=6, max_length=30)]
    email: EmailStr
    message: Annotated[str | None, Field(default=None, max_length=4000)]

    @field_validator("name", "mobile")
    @classmethod
    def require_value(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Please fill in your name, mobile number, and email.")

        return cleaned

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9+\-\s()]{6,30}", value):
            raise ValueError("Enter a valid mobile number.")

        return value


class ContactMessageOut(ApiModel):
    id: int
    name: str
    mobile: str
    email: EmailStr
    message: str | None
    is_handled: bool
    created_at: datetime


class ContactAck(ApiModel):
    id: int
    message: str
    created_at: datetime


# --------------------------------------------------------------------------- #
# Marketing stats and market data
# --------------------------------------------------------------------------- #


class StatsOut(ApiModel):
    profit_split: int
    payout_speed_hours: int
    minimum_payout: int
    accounts_funded: int
    total_rewards_paid: float


class MarketTicker(ApiModel):
    symbol: str
    last_price: float
    price_change_percent: float
    quote_volume: float


class MarketResponse(ApiModel):
    available: bool
    source: str
    fetched_at: datetime
    tickers: list[MarketTicker]
    detail: str | None = None


class HealthResponse(ApiModel):
    status: str
    environment: str
    database: str
    version: str
