"""Generation pipeline for imgcreator.

Orchestrates the image generation process from prompt to saved file.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from imgcreator.api.base import GenerationRequest, GenerationResult, GenerationStatus
from imgcreator.api.volcengine import VolcengineClient, create_client
from imgcreator.core.config import Config, ConfigLoader
from imgcreator.core.history import create_manager as create_history_manager
from imgcreator.core.template import TemplateEngine, TemplateError


@dataclass
class GenerationContext:
    """Context for a generation run."""

    prompt: str
    width: int
    height: int
    model: str
    style: str = ""
    negative_prompt: str = ""
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    seed: int | None = None
    # Path(s) to reference image(s) for image-to-image
    reference_image_path: str | list[str] | None = None

    # Template context for variable substitution
    template_context: dict[str, Any] = field(default_factory=dict)
    template_defaults: dict[str, Any] = field(default_factory=dict)

    # Series information (for history tracking)
    series: str | None = None
    item_id: str | None = None

    # Resolved values
    resolved_prompt: str = ""

    def resolve_prompt(self, use_template: bool = True) -> str:
        """Build the final prompt with style prefix and template substitution.

        Args:
            use_template: Whether to apply template substitution

        Returns:
            Resolved prompt string
        """
        prompt = self.prompt

        # Apply template substitution if context provided
        if use_template and (self.template_context or self.template_defaults):
            engine = TemplateEngine(strict=True)
            try:
                prompt = engine.render_string(
                    prompt, self.template_context, self.template_defaults
                )
            except TemplateError:
                # If template processing fails, use raw prompt
                pass

        # Add style prefix
        parts = []
        if self.style:
            parts.append(self.style)
        parts.append(prompt)
        self.resolved_prompt = ", ".join(parts) if parts else prompt
        return self.resolved_prompt

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt": self.prompt,
            "resolved_prompt": self.resolved_prompt or self.resolve_prompt(),
            "width": self.width,
            "height": self.height,
            "model": self.model,
            "style": self.style,
            "negative_prompt": self.negative_prompt,
            "output_dir": str(self.output_dir),
            "seed": self.seed,
            "reference_image_path": self.reference_image_path,
        }


@dataclass
class PipelineResult:
    """Result of a pipeline run."""

    success: bool
    output_path: Path | None = None
    duration_ms: int = 0
    context: GenerationContext | None = None
    generation_result: GenerationResult | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
        }
        if self.context:
            result["context"] = self.context.to_dict()
        if self.generation_result:
            result["request_id"] = self.generation_result.request_id
            result["seed"] = self.generation_result.seed
        return result


def generate_filename(prompt: str, timestamp: datetime | None = None) -> str:
    """Generate a filename from prompt and timestamp.

    Format: {timestamp}_{prompt_hash}.png

    Args:
        prompt: The generation prompt
        timestamp: Optional timestamp (defaults to now)

    Returns:
        Generated filename
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Create short hash of prompt
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]

    # Format timestamp
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S")

    return f"{ts_str}_{prompt_hash}.png"


class GenerationPipeline:
    """Orchestrates image generation from config to saved file."""

    def __init__(
        self,
        config: Config | None = None,
        client: VolcengineClient | None = None,
        verbose: bool = False,
        project_path: Path | None = None,
    ):
        """Initialize the pipeline.

        Args:
            config: Configuration object (loads from project if not provided)
            client: API client (creates default if not provided)
            verbose: Enable verbose logging
            project_path: Project directory path (for history tracking)
        """
        self.config = config
        self.client = client
        self.verbose = verbose
        self.project_path = project_path or Path.cwd()
        self._owns_client = False

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[pipeline] {message}")

    def _ensure_config(self) -> Config:
        """Ensure config is loaded."""
        if self.config is None:
            loader = ConfigLoader(project_path=self.project_path, verbose=self.verbose)
            self.config = loader.load()
        return self.config

    def _ensure_client(self) -> VolcengineClient:
        """Ensure API client is available."""
        if self.client is None:
            config = self._ensure_config()
            self.client = create_client(
                timeout=config.api.timeout,
                max_retries=config.api.max_retries,
                retry_delay=config.api.retry_delay,
                verbose=self.verbose,
            )
            self._owns_client = True
        return self.client

    def close(self) -> None:
        """Close resources."""
        if self._owns_client and self.client is not None:
            self.client.close()
            self.client = None

    def __enter__(self) -> "GenerationPipeline":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def create_context(
        self,
        prompt: str | None = None,
        width: int | None = None,
        height: int | None = None,
        model: str | None = None,
        style: str | None = None,
        negative_prompt: str | None = None,
        output_dir: Path | None = None,
        seed: int | None = None,
        reference_image_path: str | None = None,
    ) -> GenerationContext:
        """Create a generation context with config defaults.

        Args:
            prompt: Override prompt (uses config default if None)
            width: Override width
            height: Override height
            model: Override model
            style: Override style
            negative_prompt: Override negative prompt
            output_dir: Override output directory
            seed: Random seed for reproducibility
            reference_image_path: Path to reference image for image-to-image

        Returns:
            GenerationContext with resolved values
        """
        config = self._ensure_config()

        # Resolve reference_image_path: CLI override > config default
        resolved_reference = reference_image_path or config.defaults.reference_image

        # Use provided values or fall back to config
        ctx = GenerationContext(
            prompt=prompt or "",
            width=width or config.defaults.width,
            height=height or config.defaults.height,
            model=model or config.api.model,
            style=style if style is not None else config.defaults.style,
            negative_prompt=negative_prompt
            if negative_prompt is not None
            else config.defaults.negative_prompt,
            output_dir=output_dir or Path(config.output.base_dir),
            seed=seed,
            reference_image_path=resolved_reference,
        )

        # Resolve the final prompt
        ctx.resolve_prompt()

        return ctx

    def dry_run(self, context: GenerationContext) -> dict[str, Any]:
        """Preview what would be generated without making API call.

        Args:
            context: Generation context

        Returns:
            Dictionary with preview information
        """
        filename = generate_filename(context.resolved_prompt)
        output_path = context.output_dir / filename

        # Determine API mode
        api_mode = "Image-to-image (图生图3.0)" if context.reference_image_path else "Text-to-image"

        result = {
            "prompt": context.prompt,
            "resolved_prompt": context.resolved_prompt,
            "model": context.model,
            "dimensions": f"{context.width}x{context.height}",
            "style": context.style or "(none)",
            "negative_prompt": context.negative_prompt or "(none)",
            "seed": context.seed,
            "output_path": str(output_path),
            "api_mode": api_mode,
            "api_call": "Would call Volcengine CVProcess API",
        }

        if context.reference_image_path:
            # Store as list for consistency
            if isinstance(context.reference_image_path, str):
                result["reference_image"] = [context.reference_image_path]
            else:
                result["reference_image"] = context.reference_image_path

        return result

    def run(self, context: GenerationContext) -> PipelineResult:
        """Run the generation pipeline.

        Args:
            context: Generation context

        Returns:
            PipelineResult with outcome
        """
        import time

        start_time = time.time()

        self._log(f"Generating: {context.resolved_prompt[:50]}...")
        self._log(f"Dimensions: {context.width}x{context.height}")
        self._log(f"Model: {context.model}")

        # Ensure output directory exists
        context.output_dir.mkdir(parents=True, exist_ok=True)

        # Determine generation mode and load reference image(s) if needed
        reference_image_data = None
        if context.reference_image_path:
            from imgcreator.utils.image import ImageLoadError, load_and_encode_image

            try:
                # Resolve path relative to project root
                project_root = self.project_path

                # Handle both single image (string) and multiple images (list)
                image_paths = (
                    [context.reference_image_path]
                    if isinstance(context.reference_image_path, str)
                    else context.reference_image_path
                )

                # Load and encode all reference images
                base64_strings = []
                for img_path in image_paths:
                    base64_str, image_bytes = load_and_encode_image(img_path, project_root)
                    base64_strings.append(base64_str)

                reference_image_data = base64_strings

                if len(image_paths) == 1:
                    self._log(f"Using reference image: {image_paths[0]}")
                else:
                    paths_str = ', '.join(image_paths)
                    self._log(f"Using {len(image_paths)} reference images: {paths_str}")
                self._log("Mode: Image-to-image (图生图3.0)")
            except ImageLoadError as e:
                self._log(f"Failed to load reference image: {e}")
                return PipelineResult(
                    success=False,
                    duration_ms=int((time.time() - start_time) * 1000),
                    context=context,
                    error_message=str(e),
                )
        else:
            self._log("Mode: Text-to-image")

        # Create API request
        request = GenerationRequest(
            prompt=context.resolved_prompt,
            width=context.width,
            height=context.height,
            model=context.model,
            negative_prompt=context.negative_prompt,
            seed=context.seed,
            reference_image_path=context.reference_image_path,
            reference_image_data=reference_image_data,
        )

        # Call API
        client = self._ensure_client()
        result = client.generate(request)

        duration_ms = int((time.time() - start_time) * 1000)

        if result.status != GenerationStatus.SUCCESS:
            self._log(f"Generation failed: {result.error_message}")

            # Record failed generation in history
            try:
                history_manager = create_history_manager(project_path=self.project_path)
                history_manager.record(
                    prompt=context.prompt,
                    resolved_prompt=context.resolved_prompt,
                    model=context.model,
                    params={
                        "width": context.width,
                        "height": context.height,
                        "style": context.style,
                        "negative_prompt": context.negative_prompt,
                        "seed": context.seed,
                    },
                    status="failed",
                    duration_ms=duration_ms,
                    series=context.series,
                    item_id=context.item_id,
                    error_message=result.error_message,
                    request_id=result.request_id,
                )
            except Exception:
                # Don't fail if history recording fails
                pass

            return PipelineResult(
                success=False,
                duration_ms=duration_ms,
                context=context,
                generation_result=result,
                error_message=result.error_message,
            )

        # Save image
        filename = generate_filename(context.resolved_prompt)
        output_path = context.output_dir / filename

        if result.image:
            output_path.write_bytes(result.image)
            self._log(f"Saved: {output_path}")

        # Record successful generation in history
        try:
            history_manager = create_history_manager(project_path=self.project_path)
            history_manager.record(
                prompt=context.prompt,
                resolved_prompt=context.resolved_prompt,
                model=context.model,
                params={
                    "width": context.width,
                    "height": context.height,
                    "style": context.style,
                    "negative_prompt": context.negative_prompt,
                    "seed": context.seed,
                },
                output_path=output_path,
                status="success",
                duration_ms=duration_ms,
                series=context.series,
                item_id=context.item_id,
                request_id=result.request_id,
                seed=result.seed,
            )
        except Exception:
            # Don't fail if history recording fails
            pass

        return PipelineResult(
            success=True,
            output_path=output_path,
            duration_ms=duration_ms,
            context=context,
            generation_result=result,
        )


def create_pipeline(
    config: Config | None = None,
    verbose: bool = False,
    project_path: Path | None = None,
) -> GenerationPipeline:
    """Create a generation pipeline.

    Args:
        config: Optional configuration
        verbose: Enable verbose logging
        project_path: Project directory path

    Returns:
        Configured GenerationPipeline
    """
    return GenerationPipeline(config=config, verbose=verbose, project_path=project_path)

