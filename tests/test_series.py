"""Tests for series generation."""

from pathlib import Path

import pytest
import yaml

from imgcreator.core.series import (
    Series,
    SeriesConfig,
    SeriesItem,
    SeriesLoader,
    SeriesNotFoundError,
    SeriesValidationError,
    load_series,
)


class TestSeriesItem:
    """Tests for SeriesItem."""

    def test_item_creation(self):
        """Test creating a series item."""
        item = SeriesItem(id="home", data={"subject": "house"})
        assert item.id == "home"
        assert item.get("subject") == "house"
        assert item.get("missing", "default") == "default"

    def test_item_to_dict(self):
        """Test item serialization."""
        item = SeriesItem(id="test", data={"key": "value"})
        data = item.to_dict()
        assert data["id"] == "test"
        assert data["key"] == "value"


class TestSeriesConfig:
    """Tests for SeriesConfig."""

    def test_config_defaults(self):
        """Test config with all defaults."""
        config = SeriesConfig()
        assert config.width is None
        assert config.height is None
        assert config.model is None

    def test_config_with_values(self):
        """Test config with values."""
        config = SeriesConfig(width=512, height=512, model="test")
        assert config.width == 512
        assert config.height == 512
        assert config.model == "test"

    def test_config_to_dict(self):
        """Test config serialization."""
        config = SeriesConfig(width=256, height=256)
        data = config.to_dict()
        assert data["width"] == 256
        assert data["height"] == 256
        assert "model" not in data  # None values excluded


class TestSeries:
    """Tests for Series."""

    def test_series_creation(self):
        """Test creating a series."""
        series = Series(
            name="test",
            template="{{subject}}",
            defaults={"style": "flat"},
            items=[SeriesItem(id="item1", data={"subject": "home"})],
        )
        assert series.name == "test"
        assert len(series) == 1
        assert list(series)[0].id == "item1"

    def test_empty_series(self):
        """Test series with no items."""
        series = Series(name="empty", template="{{var}}")
        assert len(series) == 0


class TestSeriesLoader:
    """Tests for SeriesLoader."""

    @pytest.fixture
    def series_dir(self, tmp_path):
        """Create a temporary series directory."""
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        return series_dir

    def test_list_series_empty(self, tmp_path):
        """Test listing series when directory doesn't exist."""
        loader = SeriesLoader(project_path=tmp_path)
        assert loader.list_series() == []

    def test_list_series(self, series_dir):
        """Test listing series files."""
        (series_dir / "app-icons.yaml").write_text("name: app-icons")
        (series_dir / "other.yml").write_text("name: other")

        loader = SeriesLoader(project_path=series_dir.parent)
        series_list = loader.list_series()

        assert "app-icons" in series_list
        assert "other" in series_list

    def test_load_series_success(self, series_dir):
        """Test loading a valid series."""
        series_file = series_dir / "test.yaml"
        series_file.write_text(
            """
name: test-series
template: "{{style}} icon of {{subject}}"
defaults:
  style: "flat minimal"
config:
  width: 512
  height: 512
items:
  - id: home
    subject: "home house"
  - id: settings
    subject: "gear"
"""
        )

        loader = SeriesLoader(project_path=series_dir.parent)
        series = loader.load("test")

        assert series.name == "test-series"
        assert series.template == "{{style}} icon of {{subject}}"
        assert series.defaults["style"] == "flat minimal"
        assert series.config.width == 512
        assert len(series.items) == 2
        assert series.items[0].id == "home"
        assert series.items[0].get("subject") == "home house"

    def test_load_series_not_found(self, series_dir):
        """Test loading non-existent series."""
        loader = SeriesLoader(project_path=series_dir.parent)

        with pytest.raises(SeriesNotFoundError) as exc_info:
            loader.load("missing")

        assert "missing" in str(exc_info.value)

    def test_load_series_missing_name(self, series_dir):
        """Test series missing required 'name' field."""
        series_file = series_dir / "invalid.yaml"
        series_file.write_text("template: '{{var}}'\nitems: []")

        loader = SeriesLoader(project_path=series_dir.parent)

        with pytest.raises(SeriesValidationError) as exc_info:
            loader.load("invalid")

        assert "name" in str(exc_info.value).lower()

    def test_load_series_missing_template(self, series_dir):
        """Test series missing required 'template' field."""
        series_file = series_dir / "invalid.yaml"
        series_file.write_text("name: test\nitems: []")

        loader = SeriesLoader(project_path=series_dir.parent)

        with pytest.raises(SeriesValidationError) as exc_info:
            loader.load("invalid")

        assert "template" in str(exc_info.value).lower()

    def test_load_series_missing_items(self, series_dir):
        """Test series missing required 'items' field."""
        series_file = series_dir / "invalid.yaml"
        series_file.write_text("name: test\ntemplate: '{{var}}'")

        loader = SeriesLoader(project_path=series_dir.parent)

        with pytest.raises(SeriesValidationError) as exc_info:
            loader.load("invalid")

        assert "items" in str(exc_info.value).lower()

    def test_load_series_invalid_items(self, series_dir):
        """Test series with invalid items (not a list)."""
        series_file = series_dir / "invalid.yaml"
        series_file.write_text("name: test\ntemplate: '{{var}}'\nitems: {}")

        loader = SeriesLoader(project_path=series_dir.parent)

        with pytest.raises(SeriesValidationError) as exc_info:
            loader.load("invalid")

        assert "list" in str(exc_info.value).lower()

    def test_load_series_item_missing_id(self, series_dir):
        """Test series item missing 'id' field."""
        series_file = series_dir / "invalid.yaml"
        series_file.write_text(
            "name: test\ntemplate: '{{var}}'\nitems:\n  - subject: 'test'"
        )

        loader = SeriesLoader(project_path=series_dir.parent)

        with pytest.raises(SeriesValidationError) as exc_info:
            loader.load("invalid")

        assert "id" in str(exc_info.value).lower()

    def test_load_series_with_yml_extension(self, series_dir):
        """Test loading series with .yml extension."""
        series_file = series_dir / "test.yml"
        series_file.write_text(
            "name: test\ntemplate: '{{var}}'\nitems:\n  - id: item1"
        )

        loader = SeriesLoader(project_path=series_dir.parent)
        series = loader.load("test")

        assert series.name == "test"

    def test_load_default_single_series(self, series_dir):
        """Test loading default series when only one exists."""
        series_file = series_dir / "only-one.yaml"
        series_file.write_text(
            "name: only\ntemplate: '{{var}}'\nitems:\n  - id: item1"
        )

        loader = SeriesLoader(project_path=series_dir.parent)
        series = loader.load_default()

        assert series is not None
        assert series.name == "only"

    def test_load_default_multiple_series(self, series_dir):
        """Test loading default when multiple series exist."""
        (series_dir / "one.yaml").write_text(
            "name: one\ntemplate: '{{var}}'\nitems: []"
        )
        (series_dir / "two.yaml").write_text(
            "name: two\ntemplate: '{{var}}'\nitems: []"
        )

        loader = SeriesLoader(project_path=series_dir.parent)
        series = loader.load_default()

        assert series is None

    def test_load_default_no_series(self, series_dir):
        """Test loading default when no series exist."""
        loader = SeriesLoader(project_path=series_dir.parent)
        series = loader.load_default()

        assert series is None


class TestLoadSeriesFunction:
    """Tests for load_series convenience function."""

    @pytest.fixture
    def series_dir(self, tmp_path):
        """Create a temporary series directory."""
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        return series_dir

    def test_load_by_name(self, series_dir):
        """Test loading series by name."""
        series_file = series_dir / "test.yaml"
        series_file.write_text(
            "name: test\ntemplate: '{{var}}'\nitems:\n  - id: item1"
        )

        series = load_series("test", project_path=series_dir.parent)
        assert series.name == "test"

    def test_load_default_single(self, series_dir):
        """Test loading default series."""
        series_file = series_dir / "default.yaml"
        series_file.write_text(
            "name: default\ntemplate: '{{var}}'\nitems:\n  - id: item1"
        )

        series = load_series(project_path=series_dir.parent)
        assert series.name == "default"

    def test_load_default_multiple(self, series_dir):
        """Test loading default when multiple series exist."""
        (series_dir / "one.yaml").write_text(
            "name: one\ntemplate: '{{var}}'\nitems: []"
        )
        (series_dir / "two.yaml").write_text(
            "name: two\ntemplate: '{{var}}'\nitems: []"
        )

        with pytest.raises(SeriesNotFoundError) as exc_info:
            load_series(project_path=series_dir.parent)

        assert "Multiple" in str(exc_info.value)

    def test_load_default_none(self, series_dir):
        """Test loading default when no series exist."""
        with pytest.raises(SeriesNotFoundError) as exc_info:
            load_series(project_path=series_dir.parent)

        assert "No series" in str(exc_info.value)


class TestSeriesRealWorldExample:
    """Tests using real-world series examples."""

    @pytest.fixture
    def app_icons_series(self, tmp_path):
        """Create a realistic app icons series."""
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        series_file = series_dir / "app-icons.yaml"
        series_file.write_text(
            """
name: app-icons
template: "{{style}} icon of {{subject}}, {{constraints}}"
defaults:
  style: "flat, minimal, modern"
  constraints: "single color, centered, no text"
config:
  width: 512
  height: 512
items:
  - id: home
    subject: "home house"
  - id: settings
    subject: "gear cog"
  - id: profile
    subject: "person silhouette"
  - id: search
    subject: "magnifying glass"
"""
        )
        return series_dir.parent

    def test_load_app_icons(self, app_icons_series):
        """Test loading the app icons series."""
        series = load_series("app-icons", project_path=app_icons_series)

        assert series.name == "app-icons"
        assert len(series.items) == 4
        assert series.items[0].id == "home"
        assert series.items[0].get("subject") == "home house"
        assert series.config.width == 512
        assert series.defaults["style"] == "flat, minimal, modern"

