"""Password hashing and JWT access tokens."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from .config import settings

_ALGORITHM = "sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS)

    return f"pbkdf2_{_ALGORITHM}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
        algorithm = algorithm.removeprefix("pbkdf2_")
        expected = bytes.fromhex(digest_hex)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, AttributeError):
        return False

    candidate = hashlib.pbkdf2_hmac(algorithm, password.encode("utf-8"), salt, int(iterations))

    return hmac.compare_digest(candidate, expected)


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> tuple[str, int]:
    """Return a signed token and its lifetime in seconds."""

    ttl_minutes = expires_minutes or settings.access_token_ttl_minutes
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=ttl_minutes)

    payload = {
        "sub": str(subject),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    return token, ttl_minutes * 60


def decode_access_token(token: str) -> dict:
    """Decode a token, raising jwt.PyJWTError when it is invalid or expired."""

    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
