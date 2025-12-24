"""Tests for export functionality."""

from pathlib import Path

import pytest
from PIL import Image

from imgcreator.export.profiles import (
    ANDROID_PROFILE,
    IOS_PROFILE,
    ExportProfile,
    SizeProfile,
    get_profile,
    list_profiles,
    parse_custom_size,
)
from imgcreator.export.resize import (
    ExportError,
    ImageNotFoundError,
    InvalidSizeError,
    export_android,
    export_custom_size,
    export_ios,
    export_image,
    load_image,
    resize_to_size,
    resize_with_scale,
)


@pytest.fixture
def test_image(tmp_path):
    """Create a test image file."""
    image_path = tmp_path / "test.png"
    # Create a simple 100x100 red image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path, "PNG")
    return image_path


@pytest.fixture
def test_image_transparent(tmp_path):
    """Create a test image with transparency."""
    image_path = tmp_path / "test_transparent.png"
    # Create a 100x100 image with transparency
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img.save(image_path, "PNG")
    return image_path


class TestProfileDefinitions:
    """Tests for profile definitions."""

    def test_ios_profile(self):
        """Test iOS profile definition."""
        assert IOS_PROFILE.name == "ios"
        assert "@1x" in IOS_PROFILE.scales
        assert IOS_PROFILE.scales["@1x"] == 1.0
        assert IOS_PROFILE.scales["@2x"] == 2.0
        assert IOS_PROFILE.scales["@3x"] == 3.0

    def test_android_profile(self):
        """Test Android profile definition."""
        assert ANDROID_PROFILE.name == "android"
        assert "mdpi" in ANDROID_PROFILE.scales
        assert ANDROID_PROFILE.scales["mdpi"] == 1.0
        assert ANDROID_PROFILE.scales["xxxhdpi"] == 4.0

    def test_get_profile(self):
        """Test getting profile by name."""
        assert get_profile("ios") == IOS_PROFILE
        assert get_profile("android") == ANDROID_PROFILE
        assert get_profile("nonexistent") is None

    def test_list_profiles(self):
        """Test listing profiles."""
        profiles = list_profiles()
        assert "ios" in profiles
        assert "android" in profiles

    def test_parse_custom_size(self):
        """Test parsing custom size string."""
        assert parse_custom_size("100x100") == (100, 100)
        assert parse_custom_size("512x256") == (512, 256)
        assert parse_custom_size("invalid") is None
        assert parse_custom_size("100") is None
        assert parse_custom_size("0x100") is None
        assert parse_custom_size("100x0") is None


class TestImageLoading:
    """Tests for image loading."""

    def test_load_image_success(self, test_image):
        """Test loading a valid image."""
        image = load_image(test_image)
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)

    def test_load_image_not_found(self, tmp_path):
        """Test loading non-existent image."""
        with pytest.raises(ImageNotFoundError):
            load_image(tmp_path / "nonexistent.png")


class TestResizeFunctions:
    """Tests for resize functions."""

    def test_resize_with_scale(self, test_image):
        """Test resizing with scale factor."""
        image = load_image(test_image)
        resized = resize_with_scale(image, 100, 100, 2.0)

        assert resized.size == (200, 200)

    def test_resize_to_size_maintain_aspect(self, test_image):
        """Test resizing to size with aspect ratio maintained."""
        image = load_image(test_image)
        resized = resize_to_size(image, 200, 150, maintain_aspect=True)

        # Should fit within 200x150 while maintaining 1:1 aspect
        assert resized.size == (150, 150)

    def test_resize_to_size_no_maintain_aspect(self, test_image):
        """Test resizing to exact size."""
        image = load_image(test_image)
        resized = resize_to_size(image, 200, 150, maintain_aspect=False)

        assert resized.size == (200, 150)


class TestIOSExport:
    """Tests for iOS export."""

    def test_export_ios(self, test_image, tmp_path):
        """Test exporting iOS variants."""
        image = load_image(test_image)
        output_dir = tmp_path / "ios_export"

        exported = export_ios(image, "test", output_dir, 100, 100)

        assert len(exported) == 3
        assert (output_dir / "test@1x.png").exists()
        assert (output_dir / "test@2x.png").exists()
        assert (output_dir / "test@3x.png").exists()

        # Verify sizes
        img_1x = Image.open(output_dir / "test@1x.png")
        img_2x = Image.open(output_dir / "test@2x.png")
        img_3x = Image.open(output_dir / "test@3x.png")

        assert img_1x.size == (100, 100)
        assert img_2x.size == (200, 200)
        assert img_3x.size == (300, 300)

    def test_export_ios_uses_image_size(self, test_image, tmp_path):
        """Test that export uses image size if base not provided."""
        image = load_image(test_image)
        output_dir = tmp_path / "ios_export"

        exported = export_ios(image, "test", output_dir)

        assert len(exported) == 3
        img_1x = Image.open(output_dir / "test@1x.png")
        assert img_1x.size == (100, 100)


class TestAndroidExport:
    """Tests for Android export."""

    def test_export_android(self, test_image, tmp_path):
        """Test exporting Android density variants."""
        image = load_image(test_image)
        output_dir = tmp_path / "android_export"

        exported = export_android(image, "test", output_dir, 100, 100)

        assert len(exported) == 5
        assert (output_dir / "mdpi" / "test.png").exists()
        assert (output_dir / "hdpi" / "test.png").exists()
        assert (output_dir / "xhdpi" / "test.png").exists()
        assert (output_dir / "xxhdpi" / "test.png").exists()
        assert (output_dir / "xxxhdpi" / "test.png").exists()

        # Verify sizes
        mdpi = Image.open(output_dir / "mdpi" / "test.png")
        hdpi = Image.open(output_dir / "hdpi" / "test.png")
        xhdpi = Image.open(output_dir / "xhdpi" / "test.png")

        assert mdpi.size == (100, 100)
        assert hdpi.size == (150, 150)
        assert xhdpi.size == (200, 200)


class TestCustomSizeExport:
    """Tests for custom size export."""

    def test_export_custom_size(self, test_image, tmp_path):
        """Test exporting custom size."""
        image = load_image(test_image)
        output_dir = tmp_path / "custom_export"

        exported = export_custom_size(image, "test", output_dir, 200, 200)

        assert exported.exists()
        assert exported.name == "test_200x200.png"

        img = Image.open(exported)
        assert img.size == (200, 200)

    def test_export_custom_size_maintain_aspect(self, test_image, tmp_path):
        """Test custom size with aspect ratio maintained."""
        image = load_image(test_image)
        output_dir = tmp_path / "custom_export"

        exported = export_custom_size(
            image, "test", output_dir, 200, 150, maintain_aspect=True
        )

        img = Image.open(exported)
        # Should fit within 200x150, maintaining 1:1 aspect
        assert img.size == (150, 150)

    def test_export_custom_size_with_suffix(self, test_image, tmp_path):
        """Test custom size with custom suffix."""
        image = load_image(test_image)
        output_dir = tmp_path / "custom_export"

        exported = export_custom_size(
            image, "test", output_dir, 100, 100, suffix="_thumb"
        )

        assert exported.name == "test_thumb.png"


class TestTransparencyPreservation:
    """Tests for transparency preservation."""

    def test_ios_preserves_transparency(self, test_image_transparent, tmp_path):
        """Test that iOS export preserves transparency."""
        image = load_image(test_image_transparent)
        output_dir = tmp_path / "ios_export"

        export_ios(image, "test", output_dir)

        exported = Image.open(output_dir / "test@1x.png")
        assert exported.mode == "RGBA"  # Should preserve alpha channel

    def test_android_preserves_transparency(self, test_image_transparent, tmp_path):
        """Test that Android export preserves transparency."""
        image = load_image(test_image_transparent)
        output_dir = tmp_path / "android_export"

        export_android(image, "test", output_dir)

        exported = Image.open(output_dir / "mdpi" / "test.png")
        assert exported.mode == "RGBA"

    def test_custom_size_preserves_transparency(self, test_image_transparent, tmp_path):
        """Test that custom size export preserves transparency."""
        image = load_image(test_image_transparent)
        output_dir = tmp_path / "custom_export"

        exported = export_custom_size(image, "test", output_dir, 200, 200)

        img = Image.open(exported)
        assert img.mode == "RGBA"


class TestExportImage:
    """Tests for export_image function."""

    def test_export_image_ios(self, test_image, tmp_path):
        """Test exporting with iOS profile."""
        output_dir = tmp_path / "export"

        exported = export_image(test_image, IOS_PROFILE, output_dir)

        assert len(exported) == 3
        assert all(p.exists() for p in exported)

    def test_export_image_android(self, test_image, tmp_path):
        """Test exporting with Android profile."""
        output_dir = tmp_path / "export"

        exported = export_image(test_image, ANDROID_PROFILE, output_dir)

        assert len(exported) == 5
        assert all(p.exists() for p in exported)

    def test_export_image_custom_size(self, test_image, tmp_path):
        """Test exporting with custom size profile."""
        output_dir = tmp_path / "export"
        profile = SizeProfile("custom", "Custom", 150, 150)

        exported = export_image(test_image, profile, output_dir)

        assert len(exported) == 1
        assert exported[0].exists()

    def test_export_image_not_found(self, tmp_path):
        """Test exporting non-existent image."""
        output_dir = tmp_path / "export"

        with pytest.raises(ImageNotFoundError):
            export_image(tmp_path / "nonexistent.png", IOS_PROFILE, output_dir)

    def test_export_image_uses_stem_as_name(self, test_image, tmp_path):
        """Test that export uses image stem as base name."""
        output_dir = tmp_path / "export"

        exported = export_image(test_image, IOS_PROFILE, output_dir)

        # Should use "test" as base name
        assert (output_dir / "ios" / "test@1x.png").exists()


class TestAspectRatio:
    """Tests for aspect ratio handling."""

    def test_wide_image_maintains_aspect(self, tmp_path):
        """Test that wide images maintain aspect ratio."""
        # Create a 200x100 image (2:1 aspect)
        image_path = tmp_path / "wide.png"
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(image_path, "PNG")

        output_dir = tmp_path / "export"
        profile = SizeProfile("custom", "Custom", 300, 200, maintain_aspect=True)

        exported = export_image(image_path, profile, output_dir)

        result = Image.open(exported[0])
        # Should fit within 300x200, maintaining 2:1 aspect
        assert result.size == (300, 150)

    def test_tall_image_maintains_aspect(self, tmp_path):
        """Test that tall images maintain aspect ratio."""
        # Create a 100x200 image (1:2 aspect)
        image_path = tmp_path / "tall.png"
        img = Image.new("RGB", (100, 200), color="green")
        img.save(image_path, "PNG")

        output_dir = tmp_path / "export"
        profile = SizeProfile("custom", "Custom", 200, 300, maintain_aspect=True)

        exported = export_image(image_path, profile, output_dir)

        result = Image.open(exported[0])
        # Should fit within 200x300, maintaining 1:2 aspect
        assert result.size == (150, 300)

