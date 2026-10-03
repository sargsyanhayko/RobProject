"""Load configuration without exposing credentials in validation errors."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_DIR = Path(__file__).resolve().parent.parent
# Process environment wins; backend/.env wins over the existing app/.env.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR / "app" / ".env")


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    database_url: SecretStr
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=1440, gt=0)
    admin_username: str = Field(min_length=1, max_length=255)
    admin_password: SecretStr
    frontend_url: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
        except ArgumentError:
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
        if url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes")
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        if value not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM must be HS256, HS384 or HS512")
        return value

    @field_validator("admin_username", mode="before")
    @classmethod
    def strip_admin_username(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, value: SecretStr) -> SecretStr:
        length = len(value.get_secret_value().encode("utf-8"))
        if not 1 <= length <= 72:
            raise ValueError("ADMIN_PASSWORD must contain 1 to 72 UTF-8 bytes (bcrypt)")
        return value


settings = Settings(
    database_url=os.environ.get("DATABASE_URL"),
    jwt_secret_key=os.environ.get("JWT_SECRET_KEY"),
    jwt_algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
    access_token_expire_minutes=os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"),
    admin_username=os.environ.get("ADMIN_USERNAME"),
    admin_password=os.environ.get("ADMIN_PASSWORD"),
    frontend_url=os.environ.get("FRONTEND_URL", "http://localhost:5173"),
)
