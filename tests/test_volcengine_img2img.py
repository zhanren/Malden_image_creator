"""Tests for image-to-image generation in Volcengine client."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from imgcreator.api.base import GenerationRequest, GenerationStatus
from imgcreator.api.volcengine import VolcengineClient


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("VOLCENGINE_ACCESS_KEY_ID", "test_key_id")
    monkeypatch.setenv("VOLCENGINE_SECRET_ACCESS_KEY", "test_secret")


@pytest.fixture
def test_image_bytes():
    """Create test image bytes."""
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def test_image_base64(test_image_bytes):
    """Create test image base64 string."""
    return base64.b64encode(test_image_bytes).decode("utf-8")


class TestImageToImageGeneration:
    """Tests for image-to-image generation mode."""

    @patch("imgcreator.utils.image.load_and_encode_image")
    def test_generate_with_reference_image_path(
        self, mock_load, mock_env, test_image_base64
    ):
        """Test generation with reference_image_path."""
        mock_load.return_value = (test_image_base64, b"image_data")

        client = VolcengineClient(verbose=False)
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image_base64]},
                }
            ),
        )
        client._client = mock_http

        request = GenerationRequest(
            prompt="test prompt",
            reference_image_path="/path/to/image.png",
        )

        result = client.generate(request)

        assert result.status == GenerationStatus.SUCCESS
        assert len(result.images) == 1

        # Verify request was made with image-to-image parameters
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["model_version"] == "img2img_v1.0"
        assert body["req_key"] == "jimeng_i2i_v30"
        assert "image_base64" in body

    def test_generate_with_reference_image_data(self, mock_env, test_image_base64):
        """Test generation with pre-encoded reference_image_data."""
        client = VolcengineClient(verbose=False)
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image_base64]},
                }
            ),
        )
        client._client = mock_http

        request = GenerationRequest(
            prompt="test prompt",
            reference_image_data=test_image_base64.encode("utf-8"),
        )

        result = client.generate(request)

        assert result.status == GenerationStatus.SUCCESS

        # Verify image_base64 was included
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert "image_base64" in body
        assert body["image_base64"] == test_image_base64

    def test_generate_text_to_image_when_no_reference(self, mock_env, test_image_base64):
        """Test that text-to-image is used when no reference provided."""
        client = VolcengineClient(verbose=False)
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image_base64]},
                }
            ),
        )
        client._client = mock_http

        request = GenerationRequest(
            prompt="test prompt",
            model="图片生成4.0",
        )

        result = client.generate(request)

        assert result.status == GenerationStatus.SUCCESS

        # Verify text-to-image parameters
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["model_version"] == "general_v2.0"
        assert body["req_key"] == "high_aes_general_v20"
        assert "image_base64" not in body

    @patch("imgcreator.utils.image.load_and_encode_image")
    def test_image_to_image_uses_correct_req_key(
        self, mock_load, mock_env, test_image_base64
    ):
        """Test that image-to-image uses correct req_key."""
        mock_load.return_value = (test_image_base64, b"image_data")

        client = VolcengineClient(verbose=False)
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image_base64]},
                }
            ),
        )
        client._client = mock_http

        request = GenerationRequest(
            prompt="test",
            reference_image_path="/path/to/image.png",
        )

        client.generate(request)

        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["req_key"] == "jimeng_i2i_v30"
        assert body["model_version"] == "img2img_v1.0"

    @patch("imgcreator.utils.image.load_and_encode_image")
    def test_image_to_image_includes_prompt(
        self, mock_load, mock_env, test_image_base64
    ):
        """Test that prompt is included in image-to-image request."""
        mock_load.return_value = (test_image_base64, b"image_data")

        client = VolcengineClient(verbose=False)
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image_base64]},
                }
            ),
        )
        client._client = mock_http

        request = GenerationRequest(
            prompt="create similar style",
            reference_image_path="/path/to/image.png",
        )

        client.generate(request)

        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["prompt"] == "create similar style"
        assert "image_base64" in body


class TestImageLoadingInGeneration:
    """Tests for image loading during generation."""

    @patch("imgcreator.utils.image.load_and_encode_image")
    def test_loads_image_when_path_provided(
        self, mock_load, mock_env, test_image_base64
    ):
        """Test that image is loaded when reference_image_path provided."""
        mock_load.return_value = (test_image_base64, b"image_data")

        client = VolcengineClient(verbose=False)
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image_base64]},
                }
            ),
        )
        client._client = mock_http

        request = GenerationRequest(
            prompt="test",
            reference_image_path="./assets/reference.png",
        )

        client.generate(request)

        # Verify load_and_encode_image was called
        mock_load.assert_called_once_with("./assets/reference.png")

    @patch("imgcreator.utils.image.load_and_encode_image")
    def test_handles_image_load_error(self, mock_load, mock_env):
        """Test handling of image loading errors."""
        from imgcreator.api.base import GenerationError
        from imgcreator.utils.image import ImageLoadError

        mock_load.side_effect = ImageLoadError("Cannot read image file")

        client = VolcengineClient(verbose=False)

        request = GenerationRequest(
            prompt="test",
            reference_image_path="./assets/bad.png",
        )

        # GenerationError should be raised and caught by outer handler
        with pytest.raises(GenerationError) as exc_info:
            client.generate(request)

            assert "Cannot read image file" in str(exc_info.value)

