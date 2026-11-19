from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
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


def ensure_product_category_column(bind: Engine) -> None:
    """Backfill legacy catalogs and enforce categories in a single transaction."""
    with bind.begin() as connection:
        connection.execute(
            text("ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(50)")
        )
        connection.execute(
            text("UPDATE products SET category = 'other' WHERE category IS NULL")
        )
        connection.execute(
            text("ALTER TABLE products ALTER COLUMN category SET NOT NULL")
        )
        constraints = inspect(connection).get_check_constraints("products")
        category_constraint = next(
            (
                constraint
                for constraint in constraints
                if constraint["name"] == "ck_products_category_valid"
            ),
            None,
        )
        if (
            category_constraint is None
            or "'others'" not in category_constraint["sqltext"]
        ):
            # Existing catalogs may still enforce the original five categories.
            if category_constraint is not None:
                connection.execute(
                    text(
                        "ALTER TABLE products DROP CONSTRAINT ck_products_category_valid"
                    )
                )
            connection.execute(
                text(
                    "ALTER TABLE products ADD CONSTRAINT ck_products_category_valid "
                    "CHECK (category IN "
                    "('animals', 'wall', '3d_wall', 'home', 'other', 'others'))"
                )
            )


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
