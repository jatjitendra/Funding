"""ApexFund FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import settings
from .database import Base, SessionLocal, engine
from .routers import accounts, auth, checkout, contact, market, plans, stats
from .schemas import HealthResponse
from .seed import seed_plans

DESCRIPTION = """
Backend for the ApexFund demo funded-trading site.

Every endpoint replaces behaviour the static frontend used to fake in
`localStorage`: accounts, sessions, challenge plans, checkout, payout history,
contact messages and the live market ticker.

All trading, funding and payouts are simulated. No payment gateway is contacted
and no card details are stored.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        seed_plans(db)

    yield


app = FastAPI(
    title=settings.app_name,
    description=DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Flatten validation errors into a single message.

    The frontend renders one line of copy per failed form, so the first error
    message is promoted to `detail` while the full list stays available.
    """

    errors = exc.errors()
    first = errors[0]["msg"] if errors else "That request could not be processed."

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": first.removeprefix("Value error, "),
            "errors": [
                {"field": ".".join(str(part) for part in error.get("loc", ())[1:]), "message": error["msg"]}
                for error in errors
            ],
        },
    )


API_ROUTERS = (
    auth.router,
    plans.router,
    accounts.router,
    checkout.router,
    contact.router,
    market.router,
    stats.router,
)

for api_router in API_ROUTERS:
    app.include_router(api_router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        database="sqlite" if settings.is_sqlite else "postgresql",
        version=__version__,
    )


def mount_frontend(application: FastAPI) -> None:
    """Serve the static site from this process so there is a single origin.

    Only `css/`, `js/` and the top-level `.html` pages are exposed; nothing else
    in the repository (`.git`, the SQLite file, this package) is reachable.
    """

    root = settings.frontend_dir.resolve()

    if not (root / "index.html").exists():
        return

    for asset_dir in ("css", "js"):
        directory = root / asset_dir

        if directory.is_dir():
            application.mount(f"/{asset_dir}", StaticFiles(directory=directory), name=asset_dir)

    pages = {path.name for path in root.glob("*.html")}

    def serve_page(name: str) -> FileResponse:
        if name not in pages:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")

        return FileResponse(root / name)

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return serve_page("index.html")

    @application.get("/{page}.html", include_in_schema=False)
    def page(page: str) -> FileResponse:
        return serve_page(f"{Path(page).name}.html")


if settings.serve_frontend:
    mount_frontend(app)
