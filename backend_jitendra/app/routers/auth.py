"""Signup, login and session endpoints.

Replaces the localStorage-backed helpers in js/auth.js.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import CurrentUser, DbSession
from ..models import User
from ..schemas import LoginRequest, SignupRequest, TokenResponse, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _find_by_email(db: Session, email: str) -> User | None:
    # Emails are compared case-insensitively, matching the frontend's
    # email.toLowerCase() checks.
    return db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))


def _token_response(user: User) -> TokenResponse:
    token, expires_in = create_access_token(user.id)

    return TokenResponse(token=token, expires_in=expires_in, user=UserOut.model_validate(user))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: DbSession) -> TokenResponse:
    if _find_by_email(db, payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    user = User(
        name=payload.name,
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = _find_by_email(db, payload.email)

    # The same message is returned for unknown emails and wrong passwords so the
    # endpoint cannot be used to discover which addresses are registered.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been disabled.")

    return _token_response(user)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(current_user: CurrentUser) -> Response:
    """Tokens are stateless, so logging out is the client discarding its token.

    The endpoint exists so the frontend has a single call to make, and so a
    future revocation list has an obvious home.
    """

    return Response(status_code=status.HTTP_204_NO_CONTENT)
