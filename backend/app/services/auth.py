import secrets

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password, verify_password
from app.database import SessionLocal
from app.models import Admin

# Unknown usernames also go through password verification.
_dummy_password_hash = hash_password(secrets.token_urlsafe(32))


def authenticate_admin(db: Session, username: str, password: str) -> Admin | None:
    admin = db.scalar(select(Admin).where(Admin.username == username))
    password_hash = admin.password_hash if admin is not None else _dummy_password_hash
    valid_password = verify_password(password, password_hash)
    if admin is None or not valid_password or not admin.is_active:
        return None
    return admin


def ensure_default_admin() -> None:
    with SessionLocal() as db:
        exists = db.scalar(
            select(Admin.id).where(Admin.username == settings.admin_username)
        )
        if exists is not None:
            return

        # A concurrent startup must not duplicate or overwrite the admin.
        statement = (
            insert(Admin)
            .values(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password.get_secret_value()),
                is_active=True,
            )
            .on_conflict_do_nothing(index_elements=[Admin.username])
        )
        db.execute(statement)
        db.commit()
