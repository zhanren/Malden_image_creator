"""Abstract base interface for image generation providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class GenerationStatus(Enum):
    """Status of an image generation request."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class GenerationRequest:
    """Request parameters for image generation."""

    prompt: str
    width: int = 1024
    height: int = 1024
    model: str = "图片生成4.0"
    negative_prompt: str = ""
    seed: int | None = None
    num_images: int = 1

    # Additional provider-specific options
    extra: dict[str, Any] | None = None


@dataclass
class GenerationResult:
    """Result of an image generation request."""

    status: GenerationStatus
    images: list[bytes]  # Raw image data
    request_id: str | None = None
    model: str | None = None
    prompt: str | None = None
    seed: int | None = None
    duration_ms: int | None = None
    error_message: str | None = None

    # Raw response for debugging
    raw_response: dict[str, Any] | None = None

    @property
    def success(self) -> bool:
        """Check if generation was successful."""
        return self.status == GenerationStatus.SUCCESS

    @property
    def image(self) -> bytes | None:
        """Get the first generated image (convenience method)."""
        return self.images[0] if self.images else None


class ImageProviderError(Exception):
    """Base exception for image provider errors."""

    def __init__(self, message: str, provider: str = "unknown", details: dict | None = None):
        self.provider = provider
        self.details = details or {}
        super().__init__(f"[{provider}] {message}")


class AuthenticationError(ImageProviderError):
    """Authentication failed."""

    pass


class RateLimitError(ImageProviderError):
    """Rate limit exceeded."""

    def __init__(
        self, message: str, provider: str = "unknown", retry_after: int | None = None
    ):
        super().__init__(message, provider)
        self.retry_after = retry_after


class GenerationError(ImageProviderError):
    """Image generation failed."""

    pass


class TimeoutError(ImageProviderError):
    """Request timed out."""

    pass


class ImageProvider(ABC):
    """Abstract base class for image generation providers.

    Implementations should handle:
    - Authentication
    - Request formatting
    - Response parsing
    - Error handling
    - Retry logic
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and error messages."""
        pass

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate images from a text prompt.

        Args:
            request: Generation parameters

        Returns:
            GenerationResult with images or error info

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            GenerationError: If generation fails
            TimeoutError: If request times out
        """
        pass

    @abstractmethod
    def validate_config(self) -> list[str]:
        """Validate provider configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.name}>"

