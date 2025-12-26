"""Image loading and encoding utilities for reference images."""

import base64
from pathlib import Path
from typing import Tuple

from PIL import Image


class ImageLoadError(Exception):
    """Error loading or processing image."""

    pass


class ImageNotFoundError(ImageLoadError):
    """Image file not found."""

    pass


class ImageFormatError(ImageLoadError):
    """Unsupported image format."""

    pass


# Supported image formats
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"}


def load_image(path: str | Path, project_root: Path | None = None) -> bytes:
    """Load image from file path and return as bytes.

    Args:
        path: Path to image file (relative or absolute)
        project_root: Project root directory for resolving relative paths

    Returns:
        Image data as bytes

    Raises:
        ImageNotFoundError: If image file doesn't exist
        ImageFormatError: If image format is not supported
        ImageLoadError: If image cannot be read or is corrupted
    """
    path_obj = Path(path)

    # Resolve relative paths from project root
    if not path_obj.is_absolute() and project_root:
        path_obj = (project_root / path_obj).resolve()
    else:
        path_obj = path_obj.resolve()

    # Check if file exists
    if not path_obj.exists():
        raise ImageNotFoundError(
            f"Reference image not found: {path}\n"
            "Check that the file exists and path is correct."
        )

    # Check format
    if path_obj.suffix not in SUPPORTED_FORMATS:
        raise ImageFormatError(
            f"Unsupported image format: {path_obj.suffix}\n"
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    # Load and validate image
    try:
        img = Image.open(path_obj)
        img.verify()  # Verify it's a valid image
    except Exception as e:
        raise ImageLoadError(
            f"Cannot read image file: {path}\n"
            "File may be corrupted or permissions issue."
        ) from e

    # Reopen for reading (verify() closes the file)
    try:
        with Image.open(path_obj) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ("RGBA", "LA", "P"):
                # Keep transparency for PNG
                if path_obj.suffix.lower() == ".png":
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Save to bytes
            from io import BytesIO

            buffer = BytesIO()
            format_ext = path_obj.suffix.lower().lstrip(".")
            if format_ext == "jpg":
                format_ext = "jpeg"
            img.save(buffer, format=format_ext)
            return buffer.getvalue()
    except Exception as e:
        raise ImageLoadError(f"Error processing image: {path}") from e


def encode_image_base64(image_data: bytes) -> str:
    """Encode image data as base64 string.

    Args:
        image_data: Raw image bytes

    Returns:
        Base64 encoded string (without data URI prefix)
    """
    return base64.b64encode(image_data).decode("utf-8")


def load_and_encode_image(
    path: str | Path, project_root: Path | None = None
) -> Tuple[str, bytes]:
    """Load image and encode as base64.

    Args:
        path: Path to image file
        project_root: Project root directory for resolving relative paths

    Returns:
        Tuple of (base64_string, raw_bytes)

    Raises:
        ImageNotFoundError: If image file doesn't exist
        ImageFormatError: If image format is not supported
        ImageLoadError: If image cannot be read
    """
    image_data = load_image(path, project_root)
    base64_str = encode_image_base64(image_data)
    return base64_str, image_data


def resolve_image_path(
    path: str, project_root: Path | None = None
) -> Path:
    """Resolve image path (relative or absolute).

    Args:
        path: Image path string
        project_root: Project root for resolving relative paths

    Returns:
        Resolved Path object

    Raises:
        ImageNotFoundError: If resolved path doesn't exist
    """
    path_obj = Path(path)

    if not path_obj.is_absolute() and project_root:
        path_obj = (project_root / path_obj).resolve()
    else:
        path_obj = path_obj.resolve()

    if not path_obj.exists():
        raise ImageNotFoundError(
            f"Reference image not found: {path}\n"
            "Check that the file exists and path is correct."
        )

    return path_obj

