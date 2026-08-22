"""Seed the challenge plans that the frontend hard-codes in js/data.js."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Plan

PLAN_SEED: list[dict] = [
    {
        "id": "two-step-10000",
        "eval_label": "Two-Step Evaluation",
        "eval_steps": 2,
        "account_size": 10_000,
        "original_price": 499,
        "price": 399,
        "profit_split": 80,
        "phase1_profit_pct": 8,
        "phase2_profit_pct": 12,
        "max_daily_loss_pct": 5,
        "max_total_loss_pct": 10,
        "most_popular": False,
        "sort_order": 1,
    },
    {
        "id": "two-step-20000",
        "eval_label": "Two-Step Evaluation",
        "eval_steps": 2,
        "account_size": 20_000,
        "original_price": 799,
        "price": 699,
        "profit_split": 80,
        "phase1_profit_pct": 8,
        "phase2_profit_pct": 12,
        "max_daily_loss_pct": 5,
        "max_total_loss_pct": 10,
        "most_popular": True,
        "sort_order": 2,
    },
    {
        "id": "two-step-40000",
        "eval_label": "Two-Step Evaluation",
        "eval_steps": 2,
        "account_size": 40_000,
        "original_price": 999,
        "price": 899,
        "profit_split": 80,
        "phase1_profit_pct": 8,
        "phase2_profit_pct": 12,
        "max_daily_loss_pct": 5,
        "max_total_loss_pct": 10,
        "most_popular": False,
        "sort_order": 3,
    },
]


def seed_plans(db: Session) -> int:
    """Insert missing plans and refresh existing ones. Returns rows touched."""

    touched = 0

    for row in PLAN_SEED:
        plan = db.get(Plan, row["id"])

        if plan is None:
            db.add(Plan(**row, is_active=True))
            touched += 1
            continue

        for key, value in row.items():
            if getattr(plan, key) != value:
                setattr(plan, key, value)
                touched += 1

    db.commit()

    return touched
