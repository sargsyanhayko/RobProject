"""Validate local image uploads before saving their bytes in PostgreSQL."""

import warnings
from dataclasses import dataclass
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
IMAGE_MEDIA_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "GIF": "image/gif",
}


@dataclass(frozen=True)
class ProductImage:
    data: bytes
    content_type: str


def read_product_image(file: UploadFile) -> ProductImage:
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image must not exceed 5 MB",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Image file is empty")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                content_type = IMAGE_MEDIA_TYPES.get(image.format)
                if content_type is None:
                    raise ValueError("Unsupported image format")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Image dimensions are too large")
                image.verify()
            # Decode pixels as well, so incomplete files do not pass header checks.
            with Image.open(BytesIO(data)) as image:
                image.load()
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a valid JPEG, PNG, WebP or GIF image (up to 20 megapixels)",
        ) from None
    return ProductImage(data=data, content_type=content_type)
