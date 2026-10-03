from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.bcrypt import BcryptHasher

from app.config import settings

password_hasher = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("bcrypt passwords must not exceed 72 UTF-8 bytes")
    return password_hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    # bcrypt must never silently truncate a password after 72 bytes.
    if len(plain_password.encode("utf-8")) > 72:
        return False
    try:
        return password_hasher.verify(plain_password, password_hash)
    except (ValueError, UnknownHashError):
        return False


def create_access_token(admin_id: int, username: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(admin_id), "username": username, "exp": expires_at},
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["sub", "username", "exp"]},
    )
    subject = payload["sub"]
    if (
        not isinstance(subject, str)
        or not subject.isascii()
        or not subject.isdecimal()
        or not 0 < int(subject) <= 2_147_483_647
        or not isinstance(payload["username"], str)
        or not payload["username"]
        or isinstance(payload["exp"], bool)
        or not isinstance(payload["exp"], (int, float))
    ):
        raise jwt.InvalidTokenError("Invalid token claims")
    return payload
