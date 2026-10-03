from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app import models  # noqa: F401 -- registers every table before create_all
from app.config import settings
from app.database import Base, engine
from app.routers import admin, auth, products
from app.services.auth import ensure_default_admin


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_default_admin()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        await run_in_threadpool(initialize_database)
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Product Catalog API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
