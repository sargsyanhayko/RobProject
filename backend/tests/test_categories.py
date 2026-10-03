from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app import main
from app.database import SessionLocal
from app.models import Product

CATEGORIES = ["animals", "wall", "3d_wall", "home", "other"]


def photo() -> dict:
    buffer = BytesIO()
    with Image.new("RGB", (8, 8), "red") as image:
        image.save(buffer, format="PNG")
    return {"file": ("photo.png", buffer.getvalue(), "image/png")}


def test_public_category_filter_before_pagination(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = []
    for category in ["wall", "animals", "home", "animals", "3d_wall", "other"]:
        response = client.post(
            "/api/admin/products",
            json={"title": category, "price": "12000.00", "category": category},
            headers=auth_headers,
        )
        assert response.status_code == 201
        created.append(response.json())
    assert client.get("/api/products").json() == created
    for category in CATEGORIES:
        expected = [product for product in created if product["category"] == category]
        response = client.get("/api/products", params={"category": category})
        assert response.status_code == 200
        assert response.json() == expected
    animals = [product for product in created if product["category"] == "animals"]
    response = client.get("/api/products?category=animals&skip=1&limit=1")
    assert response.json() == animals[1:2]
    assert (
        client.get(f"/api/products/{created[1]['id']}").json()["category"] == "animals"
    )


def test_category_update_and_omitted_patch(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    product = client.post(
        "/api/admin/products",
        json={"title": "Cat figure", "price": 12, "category": "animals"},
        headers=auth_headers,
    ).json()
    path = f"/api/admin/products/{product['id']}"
    updated = client.patch(path, json={"category": "3d_wall"}, headers=auth_headers)
    assert updated.status_code == 200
    assert updated.json()["category"] == "3d_wall"
    assert updated.json()["title"] == product["title"]
    assert client.get("/api/products?category=animals").json() == []
    assert client.get("/api/products?category=3d_wall").json() == [updated.json()]
    for changes in [{}, {"price": 15}]:
        response = client.patch(path, json=changes, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["category"] == "3d_wall"


@pytest.mark.parametrize("category", ["all", "Animals", "invalid", "", None, 1])
def test_invalid_category_never_changes_product(
    client: TestClient, auth_headers: dict[str, str], category: object
) -> None:
    response = client.post(
        "/api/admin/products",
        json={"title": "Invalid", "price": 1, "category": category},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert client.get("/api/products").json() == []
    original = client.post(
        "/api/admin/products",
        json={"title": "Valid", "price": 1, "category": "home"},
        headers=auth_headers,
    ).json()
    response = client.patch(
        f"/api/admin/products/{original['id']}",
        json={"category": category, "title": "Changed"},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert client.get(f"/api/products/{original['id']}").json() == original


@pytest.mark.parametrize("category", ["all", "Animals", "invalid", "", "null"])
def test_invalid_category_query(client: TestClient, category: str) -> None:
    assert client.get("/api/products", params={"category": category}).status_code == 422


def test_category_required_for_both_create_routes(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    fields = {"title": "Missing category", "price": "1"}
    assert (
        client.post(
            "/api/admin/products", json=fields, headers=auth_headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/products/upload",
            data=fields,
            files=photo(),
            headers=auth_headers,
        ).status_code
        == 422
    )
    assert client.get("/api/products").json() == []


def test_upload_category_validation_and_optional_patch(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    fields = {"title": "Photo product", "price": "1"}
    response = client.post(
        "/api/admin/products/upload",
        data={**fields, "category": "invalid"},
        files=photo(),
        headers=auth_headers,
    )
    assert response.status_code == 422
    original = client.post(
        "/api/admin/products/upload",
        data={**fields, "category": "animals"},
        files=photo(),
        headers=auth_headers,
    ).json()
    path = f"/api/admin/products/{original['id']}/upload"
    response = client.patch(
        path,
        data={**fields, "category": "invalid", "title": "Changed"},
        files=photo(),
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert client.get(f"/api/products/{original['id']}").json() == original
    response = client.patch(path, data=fields, files=photo(), headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["category"] == "animals"


def test_legacy_products_backfilled_without_data_loss(
    client: TestClient, auth_headers: dict[str, str], test_engine: Engine
) -> None:
    originals = []
    for title in ["Existing cat", "Existing vase"]:
        response = client.post(
            "/api/admin/products/upload",
            data={"title": title, "price": "12.34", "category": "animals"},
            files=photo(),
            headers=auth_headers,
        )
        originals.append(response.json())
    original_image = client.get(originals[0]["image_url"]).content
    with test_engine.begin() as connection:
        connection.execute(text("ALTER TABLE products DROP COLUMN category"))
    main.initialize_database()
    main.initialize_database()
    assert client.get("/api/products").json() == [
        {**product, "category": "other"} for product in originals
    ]
    assert client.get(originals[0]["image_url"]).content == original_image
    category_column = next(
        column
        for column in inspect(test_engine).get_columns("products")
        if column["name"] == "category"
    )
    assert category_column["nullable"] is False
    assert any(
        constraint["name"] == "ck_products_category_valid"
        for constraint in inspect(test_engine).get_check_constraints("products")
    )


def test_partial_migration_preserves_assigned_categories(
    client: TestClient, auth_headers: dict[str, str], test_engine: Engine
) -> None:
    ids = []
    for category in ["animals", "home"]:
        product = client.post(
            "/api/admin/products",
            json={"title": category, "price": 1, "category": category},
            headers=auth_headers,
        ).json()
        ids.append(product["id"])
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE products DROP CONSTRAINT ck_products_category_valid, "
                "ALTER COLUMN category DROP NOT NULL"
            )
        )
        connection.execute(
            text("UPDATE products SET category = NULL WHERE id = :id"),
            {"id": ids[1]},
        )
    main.initialize_database()
    main.initialize_database()
    assert client.get(f"/api/products/{ids[0]}").json()["category"] == "animals"
    assert client.get(f"/api/products/{ids[1]}").json()["category"] == "other"


@pytest.mark.parametrize("category", ["invalid", None])
def test_database_rejects_invalid_categories(
    client: TestClient, category: str | None
) -> None:
    with SessionLocal() as db:
        db.add(Product(title="Invalid category", price=1, category=category))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
