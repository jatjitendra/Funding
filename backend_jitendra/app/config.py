"""Runtime configuration, loaded from environment variables / .env file."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "ApexFund API")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = _as_bool(os.getenv("DEBUG"), self.environment == "development")

        # Defaults to a local SQLite file so the API runs with zero setup.
        # Point DATABASE_URL at Postgres for anything beyond local development:
        #   postgresql+psycopg://user:password@localhost:5432/apexfund
        self.database_url = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BACKEND_DIR / 'apexfund.db'}",
        )

        # SQLite development databases are created on demand. When Postgres owns
        # the schema (see database_postgres/), the DDL lives in versioned SQL and
        # the app must not quietly create tables that differ from it.
        self.auto_create_tables = _as_bool(os.getenv("AUTO_CREATE_TABLES"), self.is_sqlite)
        self.seed_plans_on_startup = _as_bool(os.getenv("SEED_PLANS_ON_STARTUP"), True)

        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
        self.jwt_algorithm = "HS256"
        self.access_token_ttl_minutes = _as_int(os.getenv("ACCESS_TOKEN_TTL_MINUTES"), 60 * 24 * 7)

        self.api_prefix = "/api"

        # The frontend is a static site; serving it from this process keeps the
        # whole demo on one origin, which sidesteps CORS entirely.
        self.serve_frontend = _as_bool(os.getenv("SERVE_FRONTEND"), True)
        self.frontend_dir = Path(os.getenv("FRONTEND_DIR", str(PROJECT_ROOT)))

        self.cors_origins = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://localhost:8000",
            ).split(",")
            if origin.strip()
        ]

        self.binance_base_url = os.getenv("BINANCE_BASE_URL", "https://fapi.binance.com")
        self.market_cache_seconds = float(os.getenv("MARKET_CACHE_SECONDS", "1.0"))
        self.market_timeout_seconds = float(os.getenv("MARKET_TIMEOUT_SECONDS", "4.0"))

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
