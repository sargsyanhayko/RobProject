from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.security import decode_access_token, verify_password
from app.database import SessionLocal
from app.models import Admin, Product
from app.services.auth import ensure_default_admin

PRODUCT = {
    "title": "  Laptop  ",
    "description": "Good laptop",
    "price": 1000,
    "image_url": "https://example.com/image.jpg",
}


def test_startup_creates_tables_and_one_hashed_admin(
    client: TestClient, test_engine: Engine
) -> None:
    assert client.get("/").json() == {"status": "ok"}
    assert {"admins", "products"} <= set(inspect(test_engine).get_table_names())
    with SessionLocal() as db:
        admin = db.scalar(select(Admin))
        assert admin is not None and admin.is_active
        original_hash = admin.password_hash
        assert original_hash != settings.admin_password.get_secret_value()
        assert verify_password(
            settings.admin_password.get_secret_value(), original_hash
        )
        ensure_default_admin()
        ensure_default_admin()
        db.expire_all()
        assert db.scalar(select(func.count()).select_from(Admin)) == 1
        assert db.scalar(select(Admin.password_hash)) == original_hash


def test_login_and_jwt_claims(client: TestClient, auth_headers: dict[str, str]) -> None:
    token = auth_headers["Authorization"].split(" ", 1)[1]
    claims = decode_access_token(token)
    assert claims["username"] == settings.admin_username
    assert claims["sub"] == "1"
    remaining = claims["exp"] - datetime.now(UTC).timestamp()
    assert (
        settings.access_token_expire_minutes * 60 - 10
        < remaining
        <= settings.access_token_expire_minutes * 60
    )


@pytest.mark.parametrize(
    ("username", "password"),
    [("unknown-admin", "invalid"), (None, "invalid"), (None, "x" * 73), (None, "")],
)
def test_wrong_login_is_generic(
    client: TestClient, username: str | None, password: str
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": username or settings.admin_username, "password": password},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_public_crud(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/api/products").json() == []
    created = client.post("/api/admin/products", json=PRODUCT, headers=auth_headers)
    assert created.status_code == 201
    product = created.json()
    product_id = product["id"]
    assert product["title"] == "Laptop"
    assert product["price"] == "1000.00"
    assert product["created_at"] and product["updated_at"]
    assert client.get(f"/api/products/{product_id}").json() == product
    assert client.get("/api/products").json() == [product]
    updated = client.patch(
        f"/api/admin/products/{product_id}",
        json={
            "title": "  New Laptop  ",
            "price": "950.50",
            "description": None,
            "image_url": None,
        },
        headers=auth_headers,
    )
    assert updated.status_code == 200
    updated_product = updated.json()
    assert updated_product["title"] == "New Laptop"
    assert updated_product["price"] == "950.50"
    assert updated_product["description"] is None
    assert updated_product["image_url"] is None
    assert updated_product["created_at"] == product["created_at"]
    assert datetime.fromisoformat(
        updated_product["updated_at"]
    ) > datetime.fromisoformat(product["updated_at"])
    partial = client.patch(
        f"/api/admin/products/{product_id}", json={"price": 0}, headers=auth_headers
    )
    assert partial.status_code == 200
    assert partial.json()["title"] == "New Laptop"
    assert partial.json()["price"] == "0.00"
    deleted = client.delete(f"/api/admin/products/{product_id}", headers=auth_headers)
    assert deleted.status_code == 200
    assert deleted.json() == {"message": "Product deleted"}
    assert client.get("/api/products").json() == []
    assert client.get(f"/api/products/{product_id}").status_code == 404


def test_nullable_and_zero_price_defaults(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/admin/products",
        json={"title": "Free sample", "price": 0},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["price"] == "0.00"
    assert response.json()["description"] is None
    assert response.json()["image_url"] is None


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/admin/products"),
        ("patch", "/api/admin/products/1"),
        ("delete", "/api/admin/products/1"),
    ],
)
@pytest.mark.parametrize("authorization", [None, "Basic invalid", "Bearer malformed"])
def test_every_mutation_requires_bearer(
    client: TestClient, method: str, path: str, authorization: str | None
) -> None:
    headers = {"Authorization": authorization} if authorization else {}
    response = client.request(
        method, path, json=PRODUCT if method != "delete" else None, headers=headers
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "case",
    [
        "expired",
        "wrong-signature",
        "missing-exp",
        "missing-username",
        "bad-sub",
        "large-sub",
        "wrong-algorithm",
        "missing-admin",
    ],
)
def test_invalid_jwt_is_rejected(client: TestClient, case: str) -> None:
    claims = {
        "sub": "1",
        "username": settings.admin_username,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    signing_key = settings.jwt_secret_key.get_secret_value()
    algorithm = settings.jwt_algorithm
    if case == "expired":
        claims["exp"] = datetime.now(UTC) - timedelta(minutes=1)
    elif case == "wrong-signature":
        signing_key = "another-secret-that-is-at-least-32-bytes"
    elif case == "missing-exp":
        del claims["exp"]
    elif case == "missing-username":
        del claims["username"]
    elif case == "bad-sub":
        claims["sub"] = "not-an-id"
    elif case == "large-sub":
        claims["sub"] = "999999999999999999999999999999"
    elif case == "wrong-algorithm":
        algorithm = "HS512" if algorithm != "HS512" else "HS256"
    elif case == "missing-admin":
        claims["sub"] = "999999"
    token = jwt.encode(claims, signing_key, algorithm=algorithm)
    response = client.post(
        "/api/admin/products",
        json=PRODUCT,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("remove", [False, True])
def test_disabled_or_deleted_admin_loses_access(
    client: TestClient, auth_headers: dict[str, str], remove: bool
) -> None:
    with SessionLocal() as db:
        admin = db.scalar(select(Admin))
        if remove:
            db.delete(admin)
        else:
            admin.is_active = False
        db.commit()
    assert (
        client.post(
            "/api/admin/products", json=PRODUCT, headers=auth_headers
        ).status_code
        == 401
    )
    login = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password.get_secret_value(),
        },
    )
    assert login.status_code == 401
    assert login.json() == {"detail": "Invalid credentials"}
    if not remove:
        ensure_default_admin()
        with SessionLocal() as db:
            assert db.scalar(select(Admin)).is_active is False


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "   "},
        {"title": "x" * 256},
        {"price": -1},
        {"price": "1.001"},
        {"price": "10000000000.00"},
        {"price": "NaN"},
        {"image_url": "x" * 1001},
        {"title": None},
        {"price": None},
    ],
)
def test_invalid_product_create(
    client: TestClient, auth_headers: dict[str, str], changes: dict
) -> None:
    response = client.post(
        "/api/admin/products", json={**PRODUCT, **changes}, headers=auth_headers
    )
    assert response.status_code == 422
    assert client.get("/api/products").json() == []


@pytest.mark.parametrize(
    "changes", [{"title": None}, {"price": None}, {"title": "  "}, {"price": -1}]
)
def test_invalid_patch_does_not_change_product(
    client: TestClient, auth_headers: dict[str, str], changes: dict
) -> None:
    product = client.post(
        "/api/admin/products", json=PRODUCT, headers=auth_headers
    ).json()
    response = client.patch(
        f"/api/admin/products/{product['id']}", json=changes, headers=auth_headers
    )
    assert response.status_code == 422
    assert client.get(f"/api/products/{product['id']}").json() == product


def test_missing_product(client: TestClient, auth_headers: dict[str, str]) -> None:
    responses = [
        client.get("/api/products/999999"),
        client.patch(
            "/api/admin/products/999999", json={"price": 1}, headers=auth_headers
        ),
        client.delete("/api/admin/products/999999", headers=auth_headers),
    ]
    for response in responses:
        assert response.status_code == 404
        assert response.json() == {"detail": "Product not found"}


def test_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    for title in ["First", "Second", "Third"]:
        client.post(
            "/api/admin/products",
            json={"title": title, "price": 1},
            headers=auth_headers,
        )
    response = client.get("/api/products?skip=1&limit=1")
    assert response.status_code == 200
    assert [product["title"] for product in response.json()] == ["Second"]
    assert client.get("/api/products?skip=100").json() == []
    for query in ["skip=-1", "limit=0", "limit=101"]:
        assert client.get(f"/api/products?{query}").status_code == 422


def test_database_enforces_nonnegative_price(client: TestClient) -> None:
    with SessionLocal() as db:
        db.add(Product(title="Invalid", price=-1))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_swagger_bearer_and_cors(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"
    for path, method in [
        ("/api/admin/products", "post"),
        ("/api/admin/products/{product_id}", "patch"),
        ("/api/admin/products/{product_id}", "delete"),
    ]:
        assert schema["paths"][path][method]["security"] == [{"BearerAuth": []}]
    assert "security" not in schema["paths"]["/api/products"]["get"]
    response = client.options(
        "/api/admin/products",
        headers={
            "Origin": settings.frontend_url,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == settings.frontend_url
    rejected = client.options(
        "/api/admin/products",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert rejected.status_code == 400
    assert "access-control-allow-origin" not in rejected.headers
