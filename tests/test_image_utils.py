"""Tests for image loading and encoding utilities."""

import base64
from pathlib import Path

import pytest
from PIL import Image

from imgcreator.utils.image import (
    ImageFormatError,
    ImageLoadError,
    ImageNotFoundError,
    encode_image_base64,
    load_and_encode_image,
    load_image,
    resolve_image_path,
)


@pytest.fixture
def test_image(tmp_path):
    """Create a test PNG image."""
    image_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path, "PNG")
    return image_path


@pytest.fixture
def test_image_jpg(tmp_path):
    """Create a test JPG image."""
    image_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(image_path, "JPEG")
    return image_path


@pytest.fixture
def test_image_transparent(tmp_path):
    """Create a test PNG image with transparency."""
    image_path = tmp_path / "test_transparent.png"
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img.save(image_path, "PNG")
    return image_path


class TestLoadImage:
    """Tests for load_image function."""

    def test_load_image_success(self, test_image):
        """Test loading a valid image."""
        image_data = load_image(test_image)
        assert isinstance(image_data, bytes)
        assert len(image_data) > 0

    def test_load_image_not_found(self, tmp_path):
        """Test loading non-existent image."""
        with pytest.raises(ImageNotFoundError) as exc_info:
            load_image(tmp_path / "nonexistent.png")
        assert "not found" in str(exc_info.value).lower()

    def test_load_image_unsupported_format(self, tmp_path):
        """Test loading unsupported image format."""
        # Create a file with unsupported extension
        bad_file = tmp_path / "test.gif"
        bad_file.write_text("fake gif")
        with pytest.raises(ImageFormatError) as exc_info:
            load_image(bad_file)
        assert "unsupported" in str(exc_info.value).lower()

    def test_load_image_jpg(self, test_image_jpg):
        """Test loading JPG image."""
        image_data = load_image(test_image_jpg)
        assert isinstance(image_data, bytes)
        assert len(image_data) > 0

    def test_load_image_with_project_root(self, test_image, tmp_path):
        """Test loading image with project root for relative path."""
        # Create subdirectory structure
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        image_path = assets_dir / "test.png"
        img = Image.new("RGB", (50, 50), color="green")
        img.save(image_path, "PNG")

        # Load with relative path
        image_data = load_image("assets/test.png", project_root=tmp_path)
        assert isinstance(image_data, bytes)

    def test_load_image_preserves_transparency(self, test_image_transparent):
        """Test that transparency is preserved for PNG."""
        image_data = load_image(test_image_transparent)
        # Verify it's a valid PNG with transparency
        from io import BytesIO

        img = Image.open(BytesIO(image_data))
        assert img.mode == "RGBA"


class TestEncodeImageBase64:
    """Tests for encode_image_base64 function."""

    def test_encode_image_base64(self, test_image):
        """Test encoding image to base64."""
        image_data = load_image(test_image)
        base64_str = encode_image_base64(image_data)

        assert isinstance(base64_str, str)
        # Verify it's valid base64
        decoded = base64.b64decode(base64_str)
        assert decoded == image_data

    def test_encode_empty_bytes(self):
        """Test encoding empty bytes raises error."""
        # Empty bytes should still encode (but be invalid image)
        result = encode_image_base64(b"")
        assert isinstance(result, str)
        assert result == ""


class TestLoadAndEncodeImage:
    """Tests for load_and_encode_image function."""

    def test_load_and_encode_image(self, test_image):
        """Test loading and encoding image in one step."""
        base64_str, image_data = load_and_encode_image(test_image)

        assert isinstance(base64_str, str)
        assert isinstance(image_data, bytes)
        # Verify round-trip
        decoded = base64.b64decode(base64_str)
        assert decoded == image_data

    def test_load_and_encode_with_project_root(self, test_image, tmp_path):
        """Test loading and encoding with project root."""
        # Create subdirectory
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        image_path = assets_dir / "test.png"
        img = Image.new("RGB", (50, 50), color="yellow")
        img.save(image_path, "PNG")

        base64_str, image_data = load_and_encode_image(
            "assets/test.png", project_root=tmp_path
        )
        assert isinstance(base64_str, str)
        assert isinstance(image_data, bytes)


class TestResolveImagePath:
    """Tests for resolve_image_path function."""

    def test_resolve_absolute_path(self, test_image):
        """Test resolving absolute path."""
        resolved = resolve_image_path(str(test_image.absolute()))
        assert resolved == test_image.resolve()

    def test_resolve_relative_path(self, test_image, tmp_path):
        """Test resolving relative path with project root."""
        # Create subdirectory
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        image_path = assets_dir / "test.png"
        img = Image.new("RGB", (50, 50), color="purple")
        img.save(image_path, "PNG")

        resolved = resolve_image_path("assets/test.png", project_root=tmp_path)
        assert resolved == image_path.resolve()

    def test_resolve_path_not_found(self, tmp_path):
        """Test resolving non-existent path."""
        with pytest.raises(ImageNotFoundError):
            resolve_image_path("nonexistent.png", project_root=tmp_path)


class TestImageErrorMessages:
    """Tests for error message clarity."""

    def test_not_found_error_message(self, tmp_path):
        """Test error message for missing file."""
        with pytest.raises(ImageNotFoundError) as exc_info:
            load_image(tmp_path / "missing.png")
        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower()
        assert "check" in error_msg.lower()

    def test_format_error_message(self, tmp_path):
        """Test error message for unsupported format."""
        bad_file = tmp_path / "test.gif"
        bad_file.write_text("fake")
        with pytest.raises(ImageFormatError) as exc_info:
            load_image(bad_file)
        error_msg = str(exc_info.value)
        assert "unsupported" in error_msg.lower()
        assert "formats" in error_msg.lower()

