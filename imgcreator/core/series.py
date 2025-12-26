"""Series definition and loading for batch image generation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class SeriesError(Exception):
    """Base exception for series errors."""

    pass


class SeriesNotFoundError(SeriesError):
    """Series file not found."""

    pass


class SeriesValidationError(SeriesError):
    """Series definition is invalid."""

    pass


@dataclass
class SeriesItem:
    """A single item in a series."""

    id: str
    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from item data."""
        return self.data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"id": self.id, **self.data}


@dataclass
class SeriesConfig:
    """Configuration for a series (overrides project config)."""

    width: int | None = None
    height: int | None = None
    model: str | None = None
    style: str | None = None
    negative_prompt: str | None = None
    seed: int | None = None
    # Path(s) to reference image(s) for image-to-image
    reference_image: str | list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.width is not None:
            result["width"] = self.width
        if self.height is not None:
            result["height"] = self.height
        if self.model is not None:
            result["model"] = self.model
        if self.style is not None:
            result["style"] = self.style
        if self.negative_prompt is not None:
            result["negative_prompt"] = self.negative_prompt
        if self.seed is not None:
            result["seed"] = self.seed
        if self.reference_image is not None:
            result["reference_image"] = self.reference_image
        return result


@dataclass
class Series:
    """A series definition for batch generation."""

    name: str
    template: str
    defaults: dict[str, Any] = field(default_factory=dict)
    config: SeriesConfig = field(default_factory=SeriesConfig)
    items: list[SeriesItem] = field(default_factory=list)
    file_path: Path | None = None

    def __len__(self) -> int:
        """Return number of items in series."""
        return len(self.items)

    def __iter__(self):
        """Iterate over series items."""
        return iter(self.items)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "template": self.template,
            "defaults": self.defaults,
            "config": self.config.to_dict(),
            "items": [item.to_dict() for item in self.items],
        }


class SeriesLoader:
    """Loads and validates series definitions from YAML files."""

    SERIES_DIR = "series"

    def __init__(self, project_path: Path | None = None):
        """Initialize the series loader.

        Args:
            project_path: Path to project directory (default: current directory)
        """
        self.project_path = project_path or Path.cwd()
        self.series_dir = self.project_path / self.SERIES_DIR

    def list_series(self) -> list[str]:
        """List all available series files.

        Returns:
            List of series names (without .yaml extension)
        """
        if not self.series_dir.exists():
            return []

        series_files = list(self.series_dir.glob("*.yaml")) + list(
            self.series_dir.glob("*.yml")
        )
        return [f.stem for f in series_files]

    def load(self, name: str) -> Series:
        """Load a series definition.

        Args:
            name: Series name (without extension)

        Returns:
            Series object

        Raises:
            SeriesNotFoundError: If series file not found
            SeriesValidationError: If series definition is invalid
        """
        # Try .yaml first, then .yml
        yaml_path = self.series_dir / f"{name}.yaml"
        if not yaml_path.exists():
            yaml_path = self.series_dir / f"{name}.yml"
            if not yaml_path.exists():
                available = self.list_series()
                raise SeriesNotFoundError(
                    f"Series '{name}' not found in {self.series_dir}.\n"
                    f"Available series: {', '.join(available) if available else 'none'}"
                )

        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SeriesValidationError(f"Invalid YAML in {yaml_path}: {e}")
        except OSError as e:
            raise SeriesError(f"Cannot read {yaml_path}: {e}")

        if not data:
            raise SeriesValidationError(f"Empty series file: {yaml_path}")

        # Validate required fields
        if "name" not in data:
            raise SeriesValidationError(f"Missing 'name' field in {yaml_path}")

        if "template" not in data:
            raise SeriesValidationError(f"Missing 'template' field in {yaml_path}")

        if "items" not in data:
            raise SeriesValidationError(f"Missing 'items' field in {yaml_path}")

        # Build Series object
        series = Series(
            name=data["name"],
            template=data["template"],
            defaults=data.get("defaults", {}),
            file_path=yaml_path,
        )

        # Parse config
        config_data = data.get("config", {})
        series.config = SeriesConfig(
            width=config_data.get("width"),
            height=config_data.get("height"),
            model=config_data.get("model"),
            style=config_data.get("style"),
            negative_prompt=config_data.get("negative_prompt"),
            seed=config_data.get("seed"),
            reference_image=config_data.get("reference_image"),
        )

        # Also check for reference_image at series level (for convenience)
        if "reference_image" in data and not series.config.reference_image:
            series.config.reference_image = data.get("reference_image")

        # Parse items
        items_data = data.get("items", [])
        if not isinstance(items_data, list):
            raise SeriesValidationError("'items' must be a list")

        for idx, item_data in enumerate(items_data):
            if not isinstance(item_data, dict):
                raise SeriesValidationError(f"Item {idx} must be a dictionary")

            if "id" not in item_data:
                raise SeriesValidationError(f"Item {idx} missing 'id' field")

            item = SeriesItem(
                id=item_data["id"],
                data={k: v for k, v in item_data.items() if k != "id"},
            )
            series.items.append(item)

        return series

    def load_default(self) -> Series | None:
        """Load the default series (if only one exists).

        Returns:
            Series object or None if multiple or no series found
        """
        series_list = self.list_series()

        if len(series_list) == 1:
            return self.load(series_list[0])

        return None


def load_series(name: str | None = None, project_path: Path | None = None) -> Series:
    """Load a series by name or default.

    Args:
        name: Series name (None for default)
        project_path: Project directory path

    Returns:
        Series object

    Raises:
        SeriesError: If series not found or invalid
    """
    loader = SeriesLoader(project_path=project_path)

    if name:
        return loader.load(name)

    # Try to load default
    series = loader.load_default()
    if series is None:
        available = loader.list_series()
        if not available:
            raise SeriesNotFoundError(
                f"No series found in {loader.series_dir}.\n"
                "Create a series file in the 'series/' directory."
            )
        raise SeriesNotFoundError(
            f"Multiple series found: {', '.join(available)}.\n"
            "Specify which series to use with --series <name>"
        )

    return series

