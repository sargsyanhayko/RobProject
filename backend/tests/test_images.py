from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import Engine, inspect, text

from app import main
from app.database import SessionLocal
from app.models import Product
from app.services import images


def image_bytes(format: str = "PNG", color: str = "red") -> bytes:
    buffer = BytesIO()
    with Image.new("RGB", (8, 8), color) as image:
        image.save(buffer, format=format)
    return buffer.getvalue()


@pytest.mark.parametrize(
    "format,content_type",
    [
        ("PNG", "image/png"),
        ("JPEG", "image/jpeg"),
        ("WEBP", "image/webp"),
        ("GIF", "image/gif"),
    ],
)
def test_local_photo_is_stored_in_database_and_publicly_visible(
    client: TestClient, auth_headers: dict[str, str], format: str, content_type: str
) -> None:
    photo = image_bytes(format)
    response = client.post(
        "/api/admin/products/upload",
        data={
            "title": "  Photo product  ",
            "price": "10.50",
            "category": "animals",
            "description": "From my computer",
        },
        files={"file": ("../../local-photo", photo, "application/octet-stream")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    product = response.json()
    assert product["title"] == "Photo product"
    assert product["price"] == "10.50"
    assert product["image_url"] == f"/api/products/{product['id']}/image"
    assert "image_data" not in product
    with SessionLocal() as db:
        stored = db.get(Product, product["id"])
        assert "image_data" in inspect(stored).unloaded
        assert stored.image_data == photo
        assert stored.image_content_type == content_type
    image = client.get(product["image_url"])
    assert image.status_code == 200
    assert image.content == photo
    assert image.headers["content-type"] == content_type
    assert image.headers["x-content-type-options"] == "nosniff"
    assert client.get("/api/products").json()[0]["image_url"] == product["image_url"]


def test_replace_photo_and_edit_metadata(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original = image_bytes()
    product = client.post(
        "/api/admin/products/upload",
        data={
            "category": "animals",
            "title": "Original",
            "price": "20",
            "description": "Old description",
        },
        files={"file": ("old.png", original, "image/png")},
        headers=auth_headers,
    ).json()
    new_photo = image_bytes("JPEG", "blue")
    updated = client.patch(
        f"/api/admin/products/{product['id']}/upload",
        data={
            "category": "wall",
            "title": "Changed",
            "price": "15.99",
            "description": "",
        },
        files={"file": ("new.jpg", new_photo, "image/jpeg")},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Changed"
    assert updated.json()["category"] == "wall"
    assert updated.json()["price"] == "15.99"
    assert updated.json()["description"] is None
    assert client.get(product["image_url"]).content == new_photo
    with SessionLocal() as db:
        stored = db.get(Product, product["id"])
        assert stored.image_data == new_photo
        assert stored.image_content_type == "image/jpeg"
    metadata = client.patch(
        f"/api/admin/products/{product['id']}",
        json={"description": "Only text changed"},
        headers=auth_headers,
    )
    assert metadata.status_code == 200
    assert metadata.json()["category"] == "wall"
    assert client.get(product["image_url"]).content == new_photo


def test_clearing_image_removes_database_bytes(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    product = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", image_bytes(), "image/png")},
        headers=auth_headers,
    ).json()
    response = client.patch(
        f"/api/admin/products/{product['id']}",
        json={"image_url": None},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["image_url"] is None
    assert client.get(product["image_url"]).status_code == 404
    with SessionLocal() as db:
        stored = db.get(Product, product["id"])
        assert stored.image_data is None
        assert stored.image_content_type is None


def test_deleting_product_also_deletes_photo(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    product = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", image_bytes(), "image/png")},
        headers=auth_headers,
    ).json()
    assert (
        client.delete(
            f"/api/admin/products/{product['id']}", headers=auth_headers
        ).status_code
        == 200
    )
    assert client.get(product["image_url"]).status_code == 404
    with SessionLocal() as db:
        assert db.get(Product, product["id"]) is None


@pytest.mark.parametrize(
    "photo,expected_status",
    [
        (b"", 400),
        (b"not a real photo", 415),
        (b'<svg xmlns="http://www.w3.org/2000/svg"></svg>', 415),
    ],
)
def test_invalid_upload_does_not_create_a_product(
    client: TestClient, auth_headers: dict[str, str], photo: bytes, expected_status: int
) -> None:
    response = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", photo, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == expected_status
    assert client.get("/api/products").json() == []


def test_large_image_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", b"x" * (images.MAX_IMAGE_BYTES + 1), "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 413
    assert client.get("/api/products").json() == []


def test_image_dimensions_limited(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(images, "MAX_IMAGE_PIXELS", 63)
    response = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", image_bytes(), "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 415


def test_failed_replacement_keeps_product_and_original_photo(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    photo = image_bytes()
    product = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", "title": "Original", "price": "1"},
        files={"file": ("photo.png", photo, "image/png")},
        headers=auth_headers,
    ).json()
    response = client.patch(
        f"/api/admin/products/{product['id']}/upload",
        data={"category": "animals", "title": "Changed", "price": "2"},
        files={"file": ("invalid.png", b"invalid", "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 415
    assert client.get(f"/api/products/{product['id']}").json() == product
    assert client.get(product["image_url"]).content == photo


@pytest.mark.parametrize(
    "fields",
    [
        {"title": "   ", "price": "1"},
        {"title": "Product", "price": "-1"},
        {"title": "Product", "price": "1.001"},
    ],
)
def test_upload_validates_product_fields(
    client: TestClient, auth_headers: dict[str, str], fields: dict[str, str]
) -> None:
    response = client.post(
        "/api/admin/products/upload",
        data={"category": "animals", **fields},
        files={"file": ("photo.png", image_bytes(), "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert client.get("/api/products").json() == []


@pytest.mark.parametrize(
    "method,path",
    [("post", "/api/admin/products/upload"), ("patch", "/api/admin/products/1/upload")],
)
def test_upload_requires_admin(client: TestClient, method: str, path: str) -> None:
    response = client.request(
        method,
        path,
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", image_bytes(), "image/png")},
    )
    assert response.status_code == 401


def test_missing_image_and_missing_product(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    product = client.post(
        "/api/admin/products",
        json={"category": "animals", "title": "No image", "price": 0},
        headers=auth_headers,
    ).json()
    assert client.get(f"/api/products/{product['id']}/image").json() == {
        "detail": "Product image not found"
    }
    assert client.get("/api/products/99999/image").status_code == 404
    response = client.patch(
        "/api/admin/products/99999/upload",
        data={"category": "animals", "title": "Product", "price": "1"},
        files={"file": ("photo.png", image_bytes(), "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_existing_catalog_upgraded_without_data_loss(
    client: TestClient, auth_headers: dict[str, str], test_engine: Engine
) -> None:
    product = client.post(
        "/api/admin/products",
        json={"category": "animals", "title": "Existing product", "price": "12.34"},
        headers=auth_headers,
    ).json()
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE products DROP COLUMN image_data, DROP COLUMN image_content_type"
            )
        )
    main.initialize_database()
    main.initialize_database()
    assert client.get(f"/api/products/{product['id']}").json() == product
    column_names = {
        column["name"] for column in inspect(test_engine).get_columns("products")
    }
    assert {"image_data", "image_content_type"} <= column_names


def test_swagger_has_file_picker(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    for path, method in [
        ("/api/admin/products/upload", "post"),
        ("/api/admin/products/{product_id}/upload", "patch"),
    ]:
        operation = schema["paths"][path][method]
        assert operation["security"] == [{"BearerAuth": []}]
        body = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
        body_schema = schema["components"]["schemas"][body["$ref"].rsplit("/", 1)[1]]
        assert body_schema["properties"]["file"]["format"] == "binary"
