"""Tests for the configuration system."""

import os
from unittest.mock import patch

import pytest
import yaml

from imgcreator.core.config import (
    ConfigError,
    ConfigLoader,
    ConfigNotFoundError,
    ConfigValidationError,
    deep_merge,
    dict_to_config,
    get_api_key,
    substitute_env_vars,
    validate_config,
)


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_merge_flat_dicts(self):
        """Test merging flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        base = {"api": {"provider": "volcengine", "timeout": 30}}
        override = {"api": {"timeout": 60}}
        result = deep_merge(base, override)
        assert result == {"api": {"provider": "volcengine", "timeout": 60}}

    def test_override_replaces_non_dict(self):
        """Test that non-dict values are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = deep_merge(base, override)
        assert result == {"items": [4, 5]}

    def test_base_unchanged(self):
        """Test that base dict is not mutated."""
        base = {"a": 1}
        override = {"b": 2}
        deep_merge(base, override)
        assert base == {"a": 1}


class TestEnvVarSubstitution:
    """Tests for environment variable substitution."""

    def test_substitute_simple_var(self):
        """Test substituting a simple environment variable."""
        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            result = substitute_env_vars("prefix_${MY_VAR}_suffix")
            assert result == "prefix_my_value_suffix"

    def test_substitute_with_default(self):
        """Test substituting with default value when var not set."""
        # Ensure var is not set
        os.environ.pop("UNSET_VAR", None)
        result = substitute_env_vars("${UNSET_VAR:default_value}")
        assert result == "default_value"

    def test_substitute_missing_var_raises(self):
        """Test that missing var without default raises error."""
        os.environ.pop("MISSING_VAR", None)
        with pytest.raises(ConfigError) as exc_info:
            substitute_env_vars("${MISSING_VAR}")
        assert "MISSING_VAR" in str(exc_info.value)

    def test_substitute_in_dict(self):
        """Test substituting in nested dict."""
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            result = substitute_env_vars({"api": {"key": "${API_KEY}"}})
            assert result == {"api": {"key": "secret123"}}

    def test_substitute_in_list(self):
        """Test substituting in list."""
        with patch.dict(os.environ, {"ITEM": "value"}):
            result = substitute_env_vars(["${ITEM}", "static"])
            assert result == ["value", "static"]

    def test_non_string_passthrough(self):
        """Test that non-string values pass through unchanged."""
        assert substitute_env_vars(123) == 123
        assert substitute_env_vars(None) is None
        assert substitute_env_vars(True) is True


class TestValidateConfig:
    """Tests for config validation."""

    def test_valid_config(self):
        """Test that valid config passes validation."""
        config = {
            "api": {"provider": "volcengine", "model": "图片生成4.0"},
            "defaults": {"width": 1024, "height": 1024},
        }
        errors = validate_config(config)
        assert errors == []

    def test_invalid_provider(self):
        """Test that invalid provider is caught."""
        config = {"api": {"provider": "invalid_provider"}}
        errors = validate_config(config)
        assert len(errors) == 1
        assert "provider" in errors[0].lower()

    def test_invalid_model(self):
        """Test that invalid model is caught."""
        config = {"api": {"model": "invalid_model"}}
        errors = validate_config(config)
        assert len(errors) == 1
        assert "model" in errors[0].lower()

    def test_invalid_width(self):
        """Test that invalid width is caught."""
        config = {"defaults": {"width": -100}}
        errors = validate_config(config)
        assert len(errors) == 1
        assert "width" in errors[0].lower()

    def test_invalid_height(self):
        """Test that invalid height is caught."""
        config = {"defaults": {"height": 0}}
        errors = validate_config(config)
        assert len(errors) == 1
        assert "height" in errors[0].lower()

    def test_multiple_errors(self):
        """Test that multiple errors are collected."""
        config = {
            "api": {"provider": "bad", "model": "bad"},
            "defaults": {"width": -1, "height": -1},
        }
        errors = validate_config(config)
        assert len(errors) == 4


class TestDictToConfig:
    """Tests for dict to Config conversion."""

    def test_empty_dict_uses_defaults(self):
        """Test that empty dict produces Config with defaults."""
        config = dict_to_config({})
        assert config.api.provider == "volcengine"
        assert config.api.model == "图片生成4.0"
        assert config.defaults.width == 1024
        assert config.defaults.height == 1024

    def test_dict_values_override_defaults(self):
        """Test that dict values override defaults."""
        config = dict_to_config({
            "api": {"model": "文生图3.1"},
            "defaults": {"width": 512},
        })
        assert config.api.model == "文生图3.1"
        assert config.defaults.width == 512
        # Other defaults preserved
        assert config.defaults.height == 1024


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with config file."""
        config_content = {
            "api": {"provider": "volcengine", "model": "图片生成4.0"},
            "defaults": {"width": 512, "height": 512},
        }
        config_path = tmp_path / "imgcreator.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)
        return tmp_path

    @pytest.fixture
    def temp_global_config(self, tmp_path):
        """Create a temporary global config."""
        global_dir = tmp_path / ".imgcreator"
        global_dir.mkdir()
        config_content = {
            "api": {"timeout": 120},
            "defaults": {"style": "global style"},
        }
        config_path = global_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)
        return config_path

    def test_load_project_config(self, temp_project):
        """Test loading project configuration."""
        loader = ConfigLoader(project_path=temp_project)
        config = loader.load()

        assert config.api.provider == "volcengine"
        assert config.defaults.width == 512
        assert config.defaults.height == 512

    def test_project_config_not_found(self, tmp_path):
        """Test error when project config doesn't exist."""
        loader = ConfigLoader(project_path=tmp_path)

        with pytest.raises(ConfigNotFoundError) as exc_info:
            loader.load_project_config()

        assert "imgcreator.yaml" in str(exc_info.value)
        assert "img init" in str(exc_info.value)

    def test_load_global_config(self, temp_project, temp_global_config):
        """Test loading global configuration."""
        loader = ConfigLoader(project_path=temp_project)

        # Patch the global config path
        with patch.object(ConfigLoader, "GLOBAL_CONFIG_PATH", temp_global_config):
            config = loader.load()

        # Global config should be merged
        assert config.api.timeout == 120
        # Project config takes precedence
        assert config.defaults.width == 512

    def test_config_merge_precedence(self, temp_project, temp_global_config):
        """Test that project config overrides global config."""
        # Update project config to have same key as global
        project_config_path = temp_project / "imgcreator.yaml"
        with open(project_config_path, "w") as f:
            yaml.dump({
                "api": {"timeout": 30},  # Should override global's 120
                "defaults": {"width": 512},
            }, f)

        loader = ConfigLoader(project_path=temp_project)

        with patch.object(ConfigLoader, "GLOBAL_CONFIG_PATH", temp_global_config):
            config = loader.load()

        assert config.api.timeout == 30  # Project overrides global

    def test_load_with_overrides(self, temp_project):
        """Test loading config with per-image overrides."""
        loader = ConfigLoader(project_path=temp_project)
        overrides = {"defaults": {"width": 256, "height": 256}}

        config = loader.load_with_overrides(overrides)

        assert config.defaults.width == 256
        assert config.defaults.height == 256

    def test_validation_error_raised(self, tmp_path):
        """Test that validation errors are raised."""
        config_path = tmp_path / "imgcreator.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"api": {"provider": "invalid"}}, f)

        loader = ConfigLoader(project_path=tmp_path)

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load()

        assert "provider" in str(exc_info.value).lower()

    def test_verbose_mode(self, temp_project, capsys):
        """Test that verbose mode prints config info."""
        loader = ConfigLoader(project_path=temp_project, verbose=True)
        loader.load()

        captured = capsys.readouterr()
        assert "[config]" in captured.out
        assert "Loading" in captured.out

    def test_env_var_substitution_in_config(self, tmp_path):
        """Test that environment variables are substituted in config."""
        config_path = tmp_path / "imgcreator.yaml"
        with open(config_path, "w") as f:
            yaml.dump({
                "defaults": {"style": "${TEST_STYLE:default_style}"},
            }, f)

        loader = ConfigLoader(project_path=tmp_path)

        # Without env var set
        config = loader.load()
        assert config.defaults.style == "default_style"

        # With env var set
        with patch.dict(os.environ, {"TEST_STYLE": "custom_style"}):
            loader2 = ConfigLoader(project_path=tmp_path)
            config2 = loader2.load()
            assert config2.defaults.style == "custom_style"


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_get_api_key_success(self):
        """Test getting API key when set."""
        with patch.dict(os.environ, {"VOLCENGINE_API_KEY": "test_key_123"}):
            key = get_api_key()
            assert key == "test_key_123"

    def test_get_api_key_not_set(self):
        """Test error when API key not set."""
        os.environ.pop("VOLCENGINE_API_KEY", None)
        with pytest.raises(ConfigError) as exc_info:
            get_api_key()
        assert "VOLCENGINE_API_KEY" in str(exc_info.value)


class TestYAMLComments:
    """Tests for YAML comment support."""

    def test_yaml_with_comments_loads(self, tmp_path):
        """Test that YAML files with comments load correctly."""
        config_content = """
# This is a comment
api:
  provider: volcengine  # inline comment
  model: "图片生成4.0"

# Section comment
defaults:
  width: 1024
  height: 1024
"""
        config_path = tmp_path / "imgcreator.yaml"
        config_path.write_text(config_content)

        loader = ConfigLoader(project_path=tmp_path)
        config = loader.load()

        assert config.api.provider == "volcengine"
        assert config.defaults.width == 1024

