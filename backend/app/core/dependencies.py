from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import Admin

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    bearerFormat="JWT",
    description="Paste the access_token returned by POST /api/auth/login.",
    auto_error=False,
)
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_admin(
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Admin:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = decode_access_token(credentials.credentials)
    except (InvalidTokenError, ValueError, TypeError, OverflowError):
        raise unauthorized from None

    admin = db.get(Admin, int(payload["sub"]))
    if admin is None or not admin.is_active:
        raise unauthorized
    return admin
