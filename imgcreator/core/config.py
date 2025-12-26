"""Configuration management for imgcreator.

Implements 3-layer configuration:
1. Global config: ~/.imgcreator/config.yaml
2. Project config: ./imgcreator.yaml
3. Per-image config: from series definition

Precedence: per-image > project > global
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Valid model names for Volcengine Jimeng AI
VALID_MODELS = [
    "图片生成4.0",
    "文生图3.1",
    "文生图3.0",
    "图生图3.0",
]

# Environment variable pattern: ${VAR_NAME} or ${VAR_NAME:default}
ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


class ConfigError(Exception):
    """Configuration error with helpful message."""

    pass


class ConfigValidationError(ConfigError):
    """Validation error for config values."""

    pass


class ConfigNotFoundError(ConfigError):
    """Config file not found."""

    pass


@dataclass
class APIConfig:
    """API configuration."""

    provider: str = "volcengine"
    model: str = "文生图3.0"  # Default to 文生图3.0 (req_key: jimeng_t2i_v30)
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class DefaultsConfig:
    """Default generation settings."""

    width: int = 1024
    height: int = 1024
    style: str = ""
    negative_prompt: str = ""
    # Path(s) to reference image(s) for image-to-image
    reference_image: str | list[str] | None = None


@dataclass
class OutputConfig:
    """Output configuration."""

    base_dir: str = "./output"
    naming: str = "{timestamp}_{id}"
    format: str = "png"


@dataclass
class ExportIOSConfig:
    """iOS export configuration."""

    enabled: bool = True
    scales: list[str] = field(default_factory=lambda: ["@1x", "@2x", "@3x"])


@dataclass
class ExportAndroidConfig:
    """Android export configuration."""

    enabled: bool = True
    densities: list[str] = field(
        default_factory=lambda: ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]
    )


@dataclass
class ExportConfig:
    """Export profiles configuration."""

    ios: ExportIOSConfig = field(default_factory=ExportIOSConfig)
    android: ExportAndroidConfig = field(default_factory=ExportAndroidConfig)
    custom: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Config:
    """Main configuration object."""

    api: APIConfig = field(default_factory=APIConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    # Raw dict for any additional fields
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)


def substitute_env_vars(value: Any) -> Any:
    """Substitute environment variables in string values.

    Supports:
    - ${VAR_NAME} - raises error if not set
    - ${VAR_NAME:default} - uses default if not set

    Args:
        value: Value to process (string, dict, or list)

    Returns:
        Value with environment variables substituted
    """
    if isinstance(value, str):

        def replace_env_var(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            env_value = os.environ.get(var_name)

            if env_value is not None:
                return env_value
            elif default is not None:
                return default
            else:
                raise ConfigError(
                    f"Environment variable '{var_name}' is not set. "
                    f"Set it with: export {var_name}=your_value"
                )

        return ENV_VAR_PATTERN.sub(replace_env_var, value)

    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]

    return value


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Values in override take precedence. Nested dicts are merged recursively.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def validate_config(config_dict: dict[str, Any]) -> list[str]:
    """Validate configuration values.

    Args:
        config_dict: Configuration dictionary to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Validate API config
    api = config_dict.get("api", {})
    if api:
        provider = api.get("provider")
        if provider and provider != "volcengine":
            errors.append(
                f"Invalid API provider: '{provider}'. Only 'volcengine' is supported."
            )

        model = api.get("model")
        if model and model not in VALID_MODELS:
            errors.append(
                f"Invalid model: '{model}'. Valid models: {', '.join(VALID_MODELS)}"
            )

    # Validate defaults
    defaults = config_dict.get("defaults", {})
    if defaults:
        width = defaults.get("width")
        if width is not None and (not isinstance(width, int) or width <= 0):
            errors.append(f"Invalid width: {width}. Must be a positive integer.")

        height = defaults.get("height")
        if height is not None and (not isinstance(height, int) or height <= 0):
            errors.append(f"Invalid height: {height}. Must be a positive integer.")

        reference_image = defaults.get("reference_image")
        if reference_image is not None:
            if isinstance(reference_image, str):
                # Single image path - validate it exists
                if not Path(reference_image).exists() and not Path(reference_image).is_absolute():
                    # Relative path - might be valid, just warn
                    pass
            elif isinstance(reference_image, list):
                # Multiple image paths - validate all are strings
                for img_path in reference_image:
                    if not isinstance(img_path, str):
                        errors.append(
                            "Invalid reference_image: list must contain only string paths."
                        )
                        break
            else:
                errors.append(
                    "Invalid reference_image: must be a string path or list of string paths."
                )

    return errors


def dict_to_config(config_dict: dict[str, Any]) -> Config:
    """Convert a dictionary to a Config object.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Config object
    """
    api_dict = config_dict.get("api", {})
    api = APIConfig(
        provider=api_dict.get("provider", "volcengine"),
        model=api_dict.get("model", "文生图3.0"),
        timeout=api_dict.get("timeout", 60),
        max_retries=api_dict.get("max_retries", 3),
        retry_delay=api_dict.get("retry_delay", 1.0),
    )

    defaults_dict = config_dict.get("defaults", {})
    defaults = DefaultsConfig(
        width=defaults_dict.get("width", 1024),
        height=defaults_dict.get("height", 1024),
        style=defaults_dict.get("style", ""),
        negative_prompt=defaults_dict.get("negative_prompt", ""),
        reference_image=defaults_dict.get("reference_image"),
    )

    output_dict = config_dict.get("output", {})
    output = OutputConfig(
        base_dir=output_dict.get("base_dir", "./output"),
        naming=output_dict.get("naming", "{timestamp}_{id}"),
        format=output_dict.get("format", "png"),
    )

    export_dict = config_dict.get("export", {})
    ios_dict = export_dict.get("ios", {})
    android_dict = export_dict.get("android", {})

    export = ExportConfig(
        ios=ExportIOSConfig(
            enabled=ios_dict.get("enabled", True),
            scales=ios_dict.get("scales", ["@1x", "@2x", "@3x"]),
        ),
        android=ExportAndroidConfig(
            enabled=android_dict.get("enabled", True),
            densities=android_dict.get(
                "densities", ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]
            ),
        ),
        custom=export_dict.get("custom", []),
    )

    return Config(api=api, defaults=defaults, output=output, export=export, _raw=config_dict)


class ConfigLoader:
    """Loads and merges configuration from multiple sources."""

    GLOBAL_CONFIG_PATH = Path.home() / ".imgcreator" / "config.yaml"
    PROJECT_CONFIG_NAME = "imgcreator.yaml"

    def __init__(self, project_path: Path | None = None, verbose: bool = False):
        """Initialize the config loader.

        Args:
            project_path: Path to project directory (default: current directory)
            verbose: Enable verbose output
        """
        self.project_path = project_path or Path.cwd()
        self.verbose = verbose
        self._global_config: dict[str, Any] = {}
        self._project_config: dict[str, Any] = {}
        self._loaded = False

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[config] {message}")

    def _load_yaml_file(self, path: Path) -> dict[str, Any]:
        """Load and parse a YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML as dictionary

        Raises:
            ConfigError: If file cannot be parsed
        """
        try:
            with open(path) as f:
                content = yaml.safe_load(f)
                return content if content else {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path}: {e}")
        except OSError as e:
            raise ConfigError(f"Cannot read {path}: {e}")

    def load_global_config(self) -> dict[str, Any]:
        """Load global configuration from ~/.imgcreator/config.yaml.

        Returns:
            Global config dict (empty if file doesn't exist)
        """
        if self.GLOBAL_CONFIG_PATH.exists():
            self._log(f"Loading global config: {self.GLOBAL_CONFIG_PATH}")
            self._global_config = self._load_yaml_file(self.GLOBAL_CONFIG_PATH)
        else:
            self._log("No global config found")
            self._global_config = {}

        return self._global_config

    def load_project_config(self) -> dict[str, Any]:
        """Load project configuration from ./imgcreator.yaml.

        Returns:
            Project config dict

        Raises:
            ConfigNotFoundError: If project config doesn't exist
        """
        project_config_path = self.project_path / self.PROJECT_CONFIG_NAME

        if not project_config_path.exists():
            raise ConfigNotFoundError(
                f"Project config not found: {project_config_path}\n"
                "Run 'img init' to create a new project."
            )

        self._log(f"Loading project config: {project_config_path}")
        self._project_config = self._load_yaml_file(project_config_path)
        return self._project_config

    def load(self) -> Config:
        """Load and merge all configuration layers.

        Returns:
            Merged Config object

        Raises:
            ConfigError: If configuration is invalid
        """
        # Load configs
        self.load_global_config()

        try:
            self.load_project_config()
        except ConfigNotFoundError:
            # Use defaults if no project config
            self._log("Using default configuration")
            self._project_config = {}

        # Merge: global < project
        merged = deep_merge(self._global_config, self._project_config)

        # Substitute environment variables
        merged = substitute_env_vars(merged)

        # Validate
        errors = validate_config(merged)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            raise ConfigValidationError(error_msg)

        self._loaded = True

        if self.verbose:
            self._log("Resolved configuration:")
            self._print_config(merged)

        return dict_to_config(merged)

    def load_with_overrides(self, overrides: dict[str, Any]) -> Config:
        """Load configuration with additional overrides (e.g., per-image config).

        Args:
            overrides: Override values (highest precedence)

        Returns:
            Merged Config object
        """
        base_config = self.load()

        if not overrides:
            return base_config

        # Merge overrides on top of base
        merged = deep_merge(base_config._raw, overrides)

        # Substitute environment variables in overrides
        merged = substitute_env_vars(merged)

        # Validate
        errors = validate_config(merged)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            raise ConfigValidationError(error_msg)

        if self.verbose:
            self._log("Resolved configuration with overrides:")
            self._print_config(merged)

        return dict_to_config(merged)

    def _print_config(self, config: dict[str, Any], indent: int = 2) -> None:
        """Print configuration in a readable format."""
        yaml_output = yaml.dump(config, default_flow_style=False, allow_unicode=True)
        for line in yaml_output.split("\n"):
            if line:
                print(f"{' ' * indent}{line}")

    @property
    def global_config(self) -> dict[str, Any]:
        """Get loaded global config."""
        return self._global_config

    @property
    def project_config(self) -> dict[str, Any]:
        """Get loaded project config."""
        return self._project_config


def get_api_key() -> str:
    """Get the Volcengine API key from environment.

    Returns:
        API key string

    Raises:
        ConfigError: If API key is not set
    """
    api_key = os.environ.get("VOLCENGINE_API_KEY")
    if not api_key:
        raise ConfigError(
            "VOLCENGINE_API_KEY environment variable is not set.\n"
            "Set it with: export VOLCENGINE_API_KEY=your_api_key\n"
            "Or add it to your .env file."
        )
    return api_key

