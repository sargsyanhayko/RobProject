from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DatabaseSession
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate_admin

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: DatabaseSession) -> TokenResponse:
    admin = authenticate_admin(db, data.username, data.password.get_secret_value())
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(admin.id, admin.username))
