"""Volcengine Jimeng AI (即梦AI) client for image generation.

API Documentation:
- 文生图3.0: https://www.volcengine.com/docs/85621/1616429
- 文生图3.1: https://www.volcengine.com/docs/85621/1756900
- 图生图3.0: https://www.volcengine.com/docs/85621/1747301
- General: https://www.volcengine.com/docs/85621/1537648

Implementation details:
- Endpoint: https://visual.volcengineapi.com
- Service: cv
- Action: CVProcess
- Version: 2022-08-31
- Authentication: V4 Signature (HMAC-SHA256)
- req_key varies by model:
  - 文生图3.0: jimeng_t2i_v30
  - 文生图3.1: jimeng_t2i_v31
  - 图片生成4.0: high_aes_general_v20
  - 图生图3.0: high_aes_img2img_v10
"""

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

from imgcreator.api.base import (
    AuthenticationError,
    GenerationError,
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    ImageProvider,
    ImageProviderError,
    RateLimitError,
    TimeoutError,
)


class VolcengineClient(ImageProvider):
    """Client for Volcengine Jimeng AI image generation.

    Uses V4 signature authentication.

    Environment variables:
    - VOLCENGINE_ACCESS_KEY_ID: Access Key ID
    - VOLCENGINE_SECRET_ACCESS_KEY: Secret Access Key

    Or for simple API key auth:
    - VOLCENGINE_API_KEY: API key (if supported)
    """

    # API endpoints
    BASE_URL = "https://visual.volcengineapi.com"
    SERVICE = "cv"
    REGION = "cn-north-1"
    VERSION = "2022-08-31"

    # Action for text-to-image
    ACTION_TEXT2IMG = "CVProcess"

    # Model mapping: model name -> model_version
    # Based on Volcengine API documentation:
    # - 文生图3.0: https://www.volcengine.com/docs/85621/1616429
    # - 文生图3.1: https://www.volcengine.com/docs/85621/1756900
    MODEL_MAPPING = {
        "图片生成4.0": "general_v2.0",
        "文生图3.1": "general_v1.4",
        "文生图3.0": "general_v1.3",  # 文生图3.0 uses general_v1.3
        "图生图3.0": "img2img_v1.0",
    }

    # Request key mapping: model_version -> req_key
    # Based on Volcengine API documentation:
    # - 文生图3.0 (general_v1.3): https://www.volcengine.com/docs/85621/1616429
    #   req_key must be "jimeng_t2i_v30" (fixed value per documentation)
    # - 文生图3.1 (general_v1.4): https://www.volcengine.com/docs/85621/1756900
    #   req_key must be "jimeng_t2i_v31" (fixed value per documentation)
    # - 图片生成4.0 (general_v2.0): uses high_aes_general_v20
    REQ_KEY_MAPPING = {
        "general_v2.0": "high_aes_general_v20",
        "general_v1.4": "jimeng_t2i_v31",  # For 文生图3.1
        "general_v1.3": "jimeng_t2i_v30",  # For 文生图3.0
        "img2img_v1.0": "jimeng_i2i_v30",  # For 图生图3.0
    }

    def __init__(
        self,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        verbose: bool = False,
    ):
        """Initialize the Volcengine client.

        Args:
            access_key_id: Access Key ID (or from env VOLCENGINE_ACCESS_KEY_ID)
            secret_access_key: Secret Access Key (or from env VOLCENGINE_SECRET_ACCESS_KEY)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            verbose: Enable verbose logging
        """
        self.access_key_id = access_key_id or os.environ.get("VOLCENGINE_ACCESS_KEY_ID", "")
        self.secret_access_key = secret_access_key or os.environ.get(
            "VOLCENGINE_SECRET_ACCESS_KEY", ""
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verbose = verbose

        self._client: httpx.Client | None = None

    @property
    def name(self) -> str:
        return "volcengine"

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "VolcengineClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[volcengine] {message}")

    def validate_config(self) -> list[str]:
        """Validate provider configuration."""
        errors = []

        if not self.access_key_id:
            errors.append(
                "VOLCENGINE_ACCESS_KEY_ID not set. "
                "Set it with: export VOLCENGINE_ACCESS_KEY_ID=your_key_id"
            )

        if not self.secret_access_key:
            errors.append(
                "VOLCENGINE_SECRET_ACCESS_KEY not set. "
                "Set it with: export VOLCENGINE_SECRET_ACCESS_KEY=your_secret"
            )

        return errors

    def _sign_request(
        self,
        method: str,
        action: str,
        params: dict[str, str],
        body: str,
        timestamp: datetime,
    ) -> dict[str, str]:
        """Sign request using V4 signature.

        Returns headers with authorization.
        """
        # Format timestamp
        date_stamp = timestamp.strftime("%Y%m%d")
        amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")

        # Canonical request components
        canonical_uri = "/"
        canonical_querystring = urlencode(sorted(params.items()))

        # Hash the body
        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        # Headers to sign
        host = "visual.volcengineapi.com"
        headers_to_sign = {
            "content-type": "application/json",
            "host": host,
            "x-content-sha256": payload_hash,
            "x-date": amz_date,
        }

        # Create canonical headers string
        canonical_headers = ""
        signed_headers_list = sorted(headers_to_sign.keys())
        for header in signed_headers_list:
            canonical_headers += f"{header}:{headers_to_sign[header]}\n"
        signed_headers = ";".join(signed_headers_list)

        # Create canonical request
        canonical_request = "\n".join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        # Create string to sign
        algorithm = "HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.REGION}/{self.SERVICE}/request"
        string_to_sign = "\n".join([
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        # Calculate signature
        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = sign(self.secret_access_key.encode("utf-8"), date_stamp)
        k_region = sign(k_date, self.REGION)
        k_service = sign(k_region, self.SERVICE)
        k_signing = sign(k_service, "request")
        signature = hmac.new(
            k_signing, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Create authorization header
        authorization = (
            f"{algorithm} "
            f"Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        return {
            "Content-Type": "application/json",
            "Host": host,
            "X-Content-Sha256": payload_hash,
            "X-Date": amz_date,
            "Authorization": authorization,
        }

    def _make_request(
        self, action: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        """Make a signed API request.

        Args:
            action: API action name
            body: Request body

        Returns:
            Response data

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limited
            GenerationError: If request fails
            TimeoutError: If request times out
        """
        # Validate config first
        errors = self.validate_config()
        if errors:
            raise AuthenticationError("\n".join(errors), provider=self.name)

        url = self.BASE_URL
        params = {
            "Action": action,
            "Version": self.VERSION,
        }

        body_str = json.dumps(body, ensure_ascii=False)
        timestamp = datetime.now(timezone.utc)

        headers = self._sign_request("POST", action, params, body_str, timestamp)

        full_url = f"{url}?{urlencode(params)}"

        self._log(f"Request: POST {action}")
        self._log(f"Body: {body_str[:200]}..." if len(body_str) > 200 else f"Body: {body_str}")

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    self._log(f"Retry attempt {attempt}/{self.max_retries} after {delay}s")
                    time.sleep(delay)

                response = self.client.post(
                    full_url,
                    headers=headers,
                    content=body_str,
                )

                self._log(f"Response status: {response.status_code}")

                # Parse response
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    raise GenerationError(
                        f"Invalid JSON response: {response.text[:200]}",
                        provider=self.name,
                    )

                # Check for errors
                if response.status_code == 401:
                    # Try to extract error message from different response formats
                    error_msg = "Authentication failed"
                    error_code = "401"

                    # Volcengine API error format
                    if "message" in data:
                        error_msg = data.get("message", "Authentication failed")
                        error_code = str(data.get("code", data.get("status", "401")))
                    elif "ResponseMetadata" in data:
                        error_details = data.get("ResponseMetadata", {}).get("Error", {})
                        error_msg = error_details.get("Message", "Authentication failed")
                        error_code = error_details.get("Code", "401")

                    # Log detailed error info in verbose mode
                    if self.verbose:
                        self._log(f"Authentication error details: {error_code} - {error_msg}")
                        response_str = json.dumps(data, indent=2, ensure_ascii=False)
                        self._log(f"Full response: {response_str}")
                        self._log(f"Access Key ID (first 8 chars): {self.access_key_id[:8]}...")
                        model_ver = body.get("model_version", "unknown")
                        req_key_val = body.get("req_key", "unknown")
                        self._log(f"Request body model_version: {model_ver}")
                        self._log(f"Request body req_key: {req_key_val}")

                    # Provide more specific guidance based on error code
                    if error_code == "50400":
                        # Check which model was being used
                        model_used = body.get("model_version", "unknown")
                        req_key_used = body.get("req_key", "unknown")

                        model_suggestion = ""
                        if model_used == "img2img_v1.0" or req_key_used == "jimeng_i2i_v30":
                            model_suggestion = (
                                "\n  6. You're using '图生图3.0' (image-to-image) API.\n"
                                "     Verify you have permissions for 图生图3.0 service.\n"
                                "     Documentation: https://www.volcengine.com/docs/85621/1747301\n"
                                "     If permissions are correct, check binary_data_base64 format."
                            )
                        elif model_used == "general_v2.0" or req_key_used == "high_aes_general_v20":
                            model_suggestion = (
                                "\n  6. You're using '图片生成4.0' model which may require "
                                "different permissions.\n"
                                "     Try using '文生图3.1' instead: "
                                "img generate --model '文生图3.1'\n"
                                "     Or update your config: api.model: '文生图3.1'"
                            )
                        elif model_used == "general_v1.4" or req_key_used == "jimeng_t2i_v31":
                            model_suggestion = (
                                "\n  6. You're using '文生图3.1' model. "
                                "If this fails, try '图片生成4.0':\n"
                                "     img generate --model '图片生成4.0'"
                            )

                        guidance = (
                            "Access Denied (50400) usually means:\n"
                            "  1. Your credentials are correct but lack specific permissions\n"
                            "  2. The 即梦AI (Jimeng AI) sub-service may need separate activation\n"
                            "  3. Check IAM policies for Visual AI / 智能视觉 service permissions\n"
                            "  4. Verify the service is enabled in: https://console.volcengine.com/\n"
                            "  5. Your key accessed '智能视觉' but may need "
                            "'即梦AI' specific permissions"
                            + model_suggestion
                        )
                    else:
                        guidance = (
                            "This usually means:\n"
                            "  1. Your Access Key ID or Secret Access Key is incorrect\n"
                            "  2. Your API key doesn't have permissions for Visual AI service\n"
                            "  3. The service is not enabled for your account\n"
                            "Check your Volcengine console: https://console.volcengine.com/"
                        )

                    raise AuthenticationError(
                        f"Authentication failed ({error_code}): {error_msg}.\n{guidance}",
                        provider=self.name,
                        details=data,
                    )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Rate limit exceeded",
                        provider=self.name,
                        retry_after=int(retry_after) if retry_after else None,
                    )

                if response.status_code >= 500:
                    # Server error - retry
                    raise GenerationError(
                        f"Server error: {response.status_code}",
                        provider=self.name,
                        details=data,
                    )

                if response.status_code >= 400:
                    error_msg = data.get("ResponseMetadata", {}).get("Error", {}).get(
                        "Message", str(data)
                    )
                    raise GenerationError(
                        f"API error: {error_msg}",
                        provider=self.name,
                        details=data,
                    )

                return data

            except httpx.TimeoutException as e:
                last_error = TimeoutError(
                    f"Request timed out after {self.timeout}s",
                    provider=self.name,
                )
                if attempt == self.max_retries:
                    raise last_error from e

            except httpx.RequestError as e:
                last_error = GenerationError(
                    f"Request failed: {e}",
                    provider=self.name,
                )
                if attempt == self.max_retries:
                    raise last_error from e

            except (AuthenticationError, RateLimitError):
                # Don't retry auth or rate limit errors
                raise

            except GenerationError:
                if attempt == self.max_retries:
                    raise

        # Should not reach here, but just in case
        raise last_error or GenerationError("Unknown error", provider=self.name)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate images from a text prompt or reference image.

        Args:
            request: Generation parameters (may include reference_image_path)

        Returns:
            GenerationResult with images or error info
        """
        start_time = time.time()

        # Determine generation mode: image-to-image if reference provided
        has_reference = (
            request.reference_image_path is not None
            or request.reference_image_data is not None
        )

        # Normalize reference_image_path to list for consistent handling
        reference_paths = None
        if request.reference_image_path:
            reference_paths = (
                [request.reference_image_path]
                if isinstance(request.reference_image_path, str)
                else request.reference_image_path
            )

        if has_reference:
            # Image-to-image mode: use 图生图3.0 (智能参考)
            # Documentation: https://www.volcengine.com/docs/85621/1747301
            # Required parameters per API docs:
            # - req_key: "high_aes_img2img_v10" (fixed value for 图生图3.0)
            # - model_version: "img2img_v1.0" (fixed value for 图生图3.0)
            # - prompt: text description
            # - binary_data_base64: array of base64-encoded image strings (required)
            # - width, height: output dimensions
            model_version = "img2img_v1.0"
            req_key = self.REQ_KEY_MAPPING.get(model_version, "jimeng_i2i_v30")
            self._log("Using image-to-image mode (图生图3.0)")
            self._log(
                f"图生图3.0 API format: model_version={model_version}, "
                f"req_key={req_key}"
            )
        else:
            # Text-to-image mode: use specified model or default
            model_version = self.MODEL_MAPPING.get(request.model, "general_v1.3")
            req_key = self.REQ_KEY_MAPPING.get(
                model_version, "jimeng_t2i_v30"  # Default to 文生图3.0
            )
            self._log(f"Using text-to-image mode (model: {request.model})")

        # Build request body according to Volcengine API documentation
        # Reference:
        # - 文生图3.1: https://www.volcengine.com/docs/85621/1756900
        # - 图生图3.0: https://www.volcengine.com/docs/85621/1747301
        body = {
            "req_key": req_key,
            "prompt": request.prompt,
            "model_version": model_version,
            "width": request.width,
            "height": request.height,
            "return_url": False,  # Return base64 directly
            "logo_info": {
                "add_logo": False,
            },
        }

        # Add reference image(s) for image-to-image mode (图生图3.0)
        # According to https://www.volcengine.com/docs/85621/1747301
        if has_reference:
            if request.reference_image_data:
                # Pre-encoded base64 data (list of strings)
                if isinstance(request.reference_image_data, list):
                    image_base64_list = request.reference_image_data
                else:
                    # Legacy: single base64 string (bytes or str)
                    if isinstance(request.reference_image_data, bytes):
                        image_base64_list = [request.reference_image_data.decode("utf-8")]
                    else:
                        image_base64_list = [request.reference_image_data]
            else:
                # Need to load and encode from path(s)
                from imgcreator.api.base import GenerationError
                from imgcreator.utils.image import ImageLoadError, load_and_encode_image

                image_base64_list = []
                paths_to_load = reference_paths or []

                for img_path in paths_to_load:
                    try:
                        base64_str, _ = load_and_encode_image(img_path)
                        image_base64_list.append(base64_str)
                    except ImageLoadError as e:
                        # Convert to GenerationError for consistent error handling
                        raise GenerationError(
                            f"Failed to load reference image '{img_path}': {e}",
                            provider="volcengine"
                        ) from e

            # For 图生图3.0, add binary_data_base64 to request body
            # Documentation: https://www.volcengine.com/docs/85621/1747301
            # Parameter name: "binary_data_base64" (array of string, required)
            # Value: array of base64-encoded strings (without data URI prefix)
            # Per API docs: "图片文件base64编码,需输入1张图片" (requires 1 image)
            # Note: API structure supports array. We send all provided images.
            body["binary_data_base64"] = image_base64_list

            if len(image_base64_list) == 1:
                self._log(
                    f"Added reference image for 图生图3.0 "
                    f"(base64 length: {len(image_base64_list[0])}, "
                    f"model_version: {model_version}, req_key: {req_key})"
                )
            else:
                total_length = sum(len(img) for img in image_base64_list)
                self._log(
                    f"Added {len(image_base64_list)} reference images for 图生图3.0 "
                    f"(total base64 length: {total_length}, "
                    f"model_version: {model_version}, req_key: {req_key})"
                )

        if request.negative_prompt:
            body["negative_prompt"] = request.negative_prompt

        if request.seed is not None:
            body["seed"] = request.seed

        if request.num_images > 1:
            body["batch_size"] = min(request.num_images, 4)  # Max 4

        # Log complete request body structure (truncate binary_data_base64 for readability)
        if self.verbose:
            body_for_log = body.copy()
            if "binary_data_base64" in body_for_log:
                # binary_data_base64 is an array, get first element
                b64_array = body_for_log["binary_data_base64"]
                if b64_array and len(b64_array) > 0:
                    image_b64 = b64_array[0]
                    body_for_log["binary_data_base64"] = [
                        f"{image_b64[:50]}... (truncated, total length: {len(image_b64)})"
                    ]
            self._log("=" * 60)
            self._log("Complete Request Body:")
            self._log(json.dumps(body_for_log, indent=2, ensure_ascii=False))
            self._log("=" * 60)

        self._log(f"Generating image: {request.prompt[:50]}...")

        try:
            response = self._make_request(self.ACTION_TEXT2IMG, body)

            # Parse response
            data = response.get("data", {})
            images_data = data.get("binary_data_base64", [])

            if not images_data:
                # Try alternative response format
                image_urls = data.get("image_urls", [])
                if image_urls:
                    # Download images from URLs
                    images = []
                    for url in image_urls:
                        img_response = self.client.get(url)
                        img_response.raise_for_status()
                        images.append(img_response.content)
                else:
                    return GenerationResult(
                        status=GenerationStatus.FAILED,
                        images=[],
                        request_id=response.get("ResponseMetadata", {}).get("RequestId"),
                        error_message="No images in response",
                        raw_response=response,
                    )
            else:
                # Decode base64 images
                images = [base64.b64decode(img) for img in images_data]

            duration_ms = int((time.time() - start_time) * 1000)

            self._log(f"Generated {len(images)} image(s) in {duration_ms}ms")

            return GenerationResult(
                status=GenerationStatus.SUCCESS,
                images=images,
                request_id=response.get("ResponseMetadata", {}).get("RequestId"),
                model=request.model,
                prompt=request.prompt,
                seed=data.get("seed"),
                duration_ms=duration_ms,
                raw_response=response,
            )

        except ImageProviderError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._log(f"Generation failed: {e}")

            return GenerationResult(
                status=GenerationStatus.FAILED,
                images=[],
                error_message=str(e),
                duration_ms=duration_ms,
            )


def create_client(
    timeout: int = 60,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    verbose: bool = False,
) -> VolcengineClient:
    """Create a Volcengine client with default settings.

    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_delay: Initial retry delay
        verbose: Enable verbose logging

    Returns:
        Configured VolcengineClient
    """
    return VolcengineClient(
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
        verbose=verbose,
    )

