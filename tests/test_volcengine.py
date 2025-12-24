"""Tests for the Volcengine API client."""

import base64
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from imgcreator.api.base import (
    GenerationRequest,
    GenerationStatus,
)
from imgcreator.api.volcengine import VolcengineClient, create_client


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {
        "VOLCENGINE_ACCESS_KEY_ID": "test_key_id",
        "VOLCENGINE_SECRET_ACCESS_KEY": "test_secret_key",
    }):
        yield


@pytest.fixture
def client(mock_env):
    """Create a test client."""
    return VolcengineClient(verbose=False)


@pytest.fixture
def verbose_client(mock_env):
    """Create a verbose test client."""
    return VolcengineClient(verbose=True)


class TestVolcengineClientInit:
    """Tests for client initialization."""

    def test_init_from_env(self, mock_env):
        """Test client initializes from environment variables."""
        client = VolcengineClient()
        assert client.access_key_id == "test_key_id"
        assert client.secret_access_key == "test_secret_key"

    def test_init_from_params(self):
        """Test client initializes from parameters."""
        client = VolcengineClient(
            access_key_id="param_key_id",
            secret_access_key="param_secret",
        )
        assert client.access_key_id == "param_key_id"
        assert client.secret_access_key == "param_secret"

    def test_params_override_env(self, mock_env):
        """Test that parameters override environment variables."""
        client = VolcengineClient(
            access_key_id="override_key",
            secret_access_key="override_secret",
        )
        assert client.access_key_id == "override_key"
        assert client.secret_access_key == "override_secret"

    def test_default_settings(self, mock_env):
        """Test default client settings."""
        client = VolcengineClient()
        assert client.timeout == 60
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.verbose is False

    def test_name_property(self, client):
        """Test provider name property."""
        assert client.name == "volcengine"


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_config_success(self, mock_env):
        """Test validation passes with valid config."""
        client = VolcengineClient()
        errors = client.validate_config()
        assert errors == []

    def test_validate_missing_access_key(self):
        """Test validation fails without access key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VOLCENGINE_ACCESS_KEY_ID", None)
            os.environ.pop("VOLCENGINE_SECRET_ACCESS_KEY", None)
            client = VolcengineClient()
            errors = client.validate_config()
            assert len(errors) == 2
            assert "ACCESS_KEY_ID" in errors[0]
            assert "SECRET_ACCESS_KEY" in errors[1]

    def test_validate_missing_secret_key(self):
        """Test validation fails without secret key."""
        with patch.dict(os.environ, {"VOLCENGINE_ACCESS_KEY_ID": "key"}, clear=True):
            client = VolcengineClient()
            errors = client.validate_config()
            assert len(errors) == 1
            assert "SECRET_ACCESS_KEY" in errors[0]


class TestSignatureGeneration:
    """Tests for V4 signature generation."""

    def test_sign_request_generates_headers(self, client):
        """Test that sign_request generates required headers."""
        from datetime import datetime, timezone

        timestamp = datetime(2024, 12, 24, 12, 0, 0, tzinfo=timezone.utc)
        headers = client._sign_request(
            method="POST",
            action="CVProcess",
            params={"Action": "CVProcess", "Version": "2022-08-31"},
            body='{"prompt": "test"}',
            timestamp=timestamp,
        )

        assert "Authorization" in headers
        assert "X-Date" in headers
        assert "X-Content-Sha256" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_sign_request_authorization_format(self, client):
        """Test authorization header format."""
        from datetime import datetime, timezone

        timestamp = datetime(2024, 12, 24, 12, 0, 0, tzinfo=timezone.utc)
        headers = client._sign_request(
            method="POST",
            action="CVProcess",
            params={"Action": "CVProcess"},
            body="{}",
            timestamp=timestamp,
        )

        auth = headers["Authorization"]
        assert auth.startswith("HMAC-SHA256")
        assert "Credential=" in auth
        assert "SignedHeaders=" in auth
        assert "Signature=" in auth


class TestGenerateImages:
    """Tests for image generation."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock successful response."""
        # Create a small test image (1x1 red pixel PNG)
        test_image = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100).decode()
        return {
            "ResponseMetadata": {
                "RequestId": "test-request-123",
            },
            "data": {
                "binary_data_base64": [test_image],
                "seed": 12345,
            },
        }

    def test_generate_success(self, client, mock_response):
        """Test successful image generation."""
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=mock_response),
        )

        client._client = mock_http
        request = GenerationRequest(
            prompt="test prompt",
            width=512,
            height=512,
        )
        result = client.generate(request)

        assert result.status == GenerationStatus.SUCCESS
        assert len(result.images) == 1
        assert result.request_id == "test-request-123"
        assert result.seed == 12345

    def test_generate_with_options(self, client, mock_response):
        """Test generation with all options."""
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=mock_response),
        )

        client._client = mock_http
        request = GenerationRequest(
            prompt="test prompt",
            width=1024,
            height=1024,
            model="文生图3.1",
            negative_prompt="blurry",
            seed=42,
            num_images=2,
        )
        client.generate(request)

        # Verify request body
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["prompt"] == "test prompt"
        assert body["negative_prompt"] == "blurry"
        assert body["seed"] == 42
        assert body["batch_size"] == 2

    def test_generate_authentication_error(self, client):
        """Test authentication error handling."""
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=401,
            json=MagicMock(return_value={"error": "unauthorized"}),
        )

        client._client = mock_http
        request = GenerationRequest(prompt="test")
        result = client.generate(request)

        assert result.status == GenerationStatus.FAILED
        assert "Authentication" in result.error_message

    def test_generate_rate_limit_error(self, client):
        """Test rate limit error handling."""
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=429,
            headers={"Retry-After": "60"},
            json=MagicMock(return_value={"error": "rate limited"}),
        )

        client._client = mock_http
        request = GenerationRequest(prompt="test")
        result = client.generate(request)

        assert result.status == GenerationStatus.FAILED
        assert "Rate limit" in result.error_message

    def test_generate_api_error(self, client):
        """Test API error handling."""
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=400,
            json=MagicMock(return_value={
                "ResponseMetadata": {
                    "Error": {"Message": "Invalid prompt"}
                }
            }),
        )

        client._client = mock_http
        request = GenerationRequest(prompt="test")
        result = client.generate(request)

        assert result.status == GenerationStatus.FAILED
        assert "Invalid prompt" in result.error_message


class TestRetryLogic:
    """Tests for retry logic."""

    def test_retry_on_server_error(self, client):
        """Test retry on 5xx errors."""
        mock_http = MagicMock()
        # First call fails, second succeeds
        test_image = base64.b64encode(b"test").decode()
        mock_http.post.side_effect = [
            MagicMock(
                status_code=500,
                json=MagicMock(return_value={"error": "server error"}),
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "ResponseMetadata": {"RequestId": "123"},
                    "data": {"binary_data_base64": [test_image]},
                }),
            ),
        ]

        client._client = mock_http
        with patch("time.sleep"):  # Skip actual sleep
            request = GenerationRequest(prompt="test")
            result = client.generate(request)

        assert result.status == GenerationStatus.SUCCESS
        assert mock_http.post.call_count == 2

    def test_no_retry_on_auth_error(self, client):
        """Test no retry on authentication errors."""
        mock_http = MagicMock()
        mock_http.post.return_value = MagicMock(
            status_code=401,
            json=MagicMock(return_value={"error": "unauthorized"}),
        )

        client._client = mock_http
        request = GenerationRequest(prompt="test")
        client.generate(request)

        # Should only try once
        assert mock_http.post.call_count == 1


class TestCreateClient:
    """Tests for create_client factory function."""

    def test_create_client_default(self, mock_env):
        """Test creating client with defaults."""
        client = create_client()
        assert client.timeout == 60
        assert client.max_retries == 3
        assert client.verbose is False

    def test_create_client_custom(self, mock_env):
        """Test creating client with custom settings."""
        client = create_client(
            timeout=120,
            max_retries=5,
            retry_delay=2.0,
            verbose=True,
        )
        assert client.timeout == 120
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.verbose is True


class TestContextManager:
    """Tests for context manager behavior."""

    def test_context_manager_closes_client(self, mock_env):
        """Test that context manager closes the HTTP client."""
        with VolcengineClient() as client:
            # Access client to create it
            _ = client.client
            assert client._client is not None

        # After exiting, client should be closed
        assert client._client is None

    def test_manual_close(self, mock_env):
        """Test manual close method."""
        client = VolcengineClient()
        _ = client.client
        assert client._client is not None

        client.close()
        assert client._client is None


class TestModelMapping:
    """Tests for model name mapping."""

    def test_model_mapping_exists(self):
        """Test that model mapping has expected models."""
        assert "图片生成4.0" in VolcengineClient.MODEL_MAPPING
        assert "文生图3.1" in VolcengineClient.MODEL_MAPPING
        assert "图生图3.0" in VolcengineClient.MODEL_MAPPING

    def test_default_model_mapping(self, client, mock_env):
        """Test that unknown model falls back to default."""
        mock_http = MagicMock()
        test_image = base64.b64encode(b"test").decode()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "ResponseMetadata": {"RequestId": "123"},
                "data": {"binary_data_base64": [test_image]},
            }),
        )

        client._client = mock_http
        request = GenerationRequest(prompt="test", model="unknown_model")
        client.generate(request)

        # Check request body uses default model version
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["model_version"] == "general_v2.0"

    def test_req_key_mapping_for_models(self, client, mock_env):
        """Test that req_key is correctly mapped for different models."""
        mock_http = MagicMock()
        test_image = base64.b64encode(b"test").decode()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "ResponseMetadata": {"RequestId": "123"},
                "data": {"binary_data_base64": [test_image]},
            }),
        )

        client._client = mock_http

        # Test 文生图3.1 -> general_v1.4 -> jimeng_t2i_v31 (fixed value per API docs)
        request = GenerationRequest(prompt="test", model="文生图3.1")
        client.generate(request)
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["req_key"] == "jimeng_t2i_v31"
        assert body["model_version"] == "general_v1.4"

        # Test 图片生成4.0 -> general_v2.0 -> high_aes_general_v20
        request = GenerationRequest(prompt="test", model="图片生成4.0")
        client.generate(request)
        call_args = mock_http.post.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["req_key"] == "high_aes_general_v20"
        assert body["model_version"] == "general_v2.0"


class TestVerboseMode:
    """Tests for verbose logging."""

    def test_verbose_logs_request(self, verbose_client, capsys):
        """Test that verbose mode logs request info."""
        mock_http = MagicMock()
        test_image = base64.b64encode(b"test").decode()
        mock_http.post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "ResponseMetadata": {"RequestId": "123"},
                "data": {"binary_data_base64": [test_image]},
            }),
        )

        verbose_client._client = mock_http
        request = GenerationRequest(prompt="test prompt")
        verbose_client.generate(request)

        captured = capsys.readouterr()
        assert "[volcengine]" in captured.out
        assert "Request:" in captured.out or "Generating" in captured.out

