from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    hide_parameters=True,
    connect_args={"connect_timeout": 10},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def ensure_product_image_columns(bind: Engine) -> None:
    """Add upload storage to existing catalogs without dropping their tables."""
    with bind.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE products "
                "ADD COLUMN IF NOT EXISTS image_data BYTEA, "
                "ADD COLUMN IF NOT EXISTS image_content_type VARCHAR(100)"
            )
        )


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
