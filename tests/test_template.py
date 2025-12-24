"""Tests for the template engine."""

import pytest

from imgcreator.core.template import (
    TemplateEngine,
    TemplateSyntaxError,
    VariableNotFoundError,
    create_engine,
    flatten_keys,
    get_nested_value,
    render,
    validate,
)


class TestGetNestedValue:
    """Tests for get_nested_value function."""

    def test_simple_key(self):
        """Test getting a simple key."""
        data = {"name": "test"}
        assert get_nested_value(data, "name") == "test"

    def test_nested_key(self):
        """Test getting a nested key."""
        data = {"user": {"name": "John", "age": 30}}
        assert get_nested_value(data, "user.name") == "John"
        assert get_nested_value(data, "user.age") == 30

    def test_deeply_nested_key(self):
        """Test getting a deeply nested key."""
        data = {"a": {"b": {"c": {"d": "value"}}}}
        assert get_nested_value(data, "a.b.c.d") == "value"

    def test_missing_key_raises(self):
        """Test that missing key raises KeyError."""
        data = {"name": "test"}
        with pytest.raises(KeyError):
            get_nested_value(data, "missing")

    def test_nested_missing_key_raises(self):
        """Test that missing nested key raises KeyError."""
        data = {"user": {"name": "test"}}
        with pytest.raises(KeyError):
            get_nested_value(data, "user.missing")


class TestFlattenKeys:
    """Tests for flatten_keys function."""

    def test_flat_dict(self):
        """Test flattening a flat dictionary."""
        data = {"a": 1, "b": 2}
        keys = flatten_keys(data)
        assert "a" in keys
        assert "b" in keys

    def test_nested_dict(self):
        """Test flattening a nested dictionary."""
        data = {"user": {"name": "John", "age": 30}}
        keys = flatten_keys(data)
        assert "user" in keys
        assert "user.name" in keys
        assert "user.age" in keys


class TestTemplateValidation:
    """Tests for template validation."""

    def test_valid_template(self):
        """Test validating a valid template."""
        engine = TemplateEngine()
        variables = engine.validate("Hello {{name}}")
        assert variables == ["name"]

    def test_multiple_variables(self):
        """Test template with multiple variables."""
        engine = TemplateEngine()
        variables = engine.validate("{{greeting}} {{name}}!")
        assert "greeting" in variables
        assert "name" in variables

    def test_variable_with_default(self):
        """Test template with default value."""
        engine = TemplateEngine()
        variables = engine.validate("{{name|Anonymous}}")
        assert variables == ["name"]

    def test_nested_variable(self):
        """Test template with nested variable."""
        engine = TemplateEngine()
        variables = engine.validate("{{user.name}}")
        assert variables == ["user.name"]

    def test_unbalanced_braces(self):
        """Test that unbalanced braces raise error."""
        engine = TemplateEngine()
        with pytest.raises(TemplateSyntaxError):
            engine.validate("{{name}")

    def test_no_variables(self):
        """Test template with no variables."""
        engine = TemplateEngine()
        variables = engine.validate("Hello World")
        assert variables == []


class TestBasicSubstitution:
    """Tests for basic variable substitution."""

    def test_simple_substitution(self):
        """Test simple variable substitution."""
        engine = TemplateEngine()
        result = engine.render("Hello {{name}}", {"name": "World"})

        assert result.rendered == "Hello World"
        assert "name" in result.variables_used

    def test_multiple_substitution(self):
        """Test multiple variable substitution."""
        engine = TemplateEngine()
        result = engine.render(
            "{{greeting}} {{name}}!",
            {"greeting": "Hello", "name": "World"},
        )

        assert result.rendered == "Hello World!"

    def test_same_variable_multiple_times(self):
        """Test same variable used multiple times."""
        engine = TemplateEngine()
        result = engine.render(
            "{{name}} likes {{name}}",
            {"name": "Bob"},
        )

        assert result.rendered == "Bob likes Bob"

    def test_nested_variable(self):
        """Test nested variable substitution."""
        engine = TemplateEngine()
        result = engine.render(
            "User: {{user.name}}",
            {"user": {"name": "John"}},
        )

        assert result.rendered == "User: John"


class TestDefaultValues:
    """Tests for default value handling."""

    def test_inline_default(self):
        """Test inline default value."""
        engine = TemplateEngine()
        result = engine.render("Hello {{name|World}}", {})

        assert result.rendered == "Hello World"
        assert "name" in result.defaults_applied

    def test_inline_default_with_spaces(self):
        """Test inline default with spaces in value."""
        engine = TemplateEngine()
        result = engine.render("{{greeting|Hello World}}", {})

        assert result.rendered == "Hello World"

    def test_context_overrides_inline_default(self):
        """Test that context value overrides inline default."""
        engine = TemplateEngine()
        result = engine.render(
            "{{name|Default}}",
            {"name": "Override"},
        )

        assert result.rendered == "Override"
        assert "name" in result.variables_used
        assert "name" not in result.defaults_applied

    def test_defaults_dict(self):
        """Test defaults dictionary."""
        engine = TemplateEngine()
        result = engine.render(
            "Hello {{name}}",
            {},
            defaults={"name": "World"},
        )

        assert result.rendered == "Hello World"
        assert "name" in result.defaults_applied

    def test_context_overrides_defaults_dict(self):
        """Test that context overrides defaults dict."""
        engine = TemplateEngine()
        result = engine.render(
            "{{name}}",
            {"name": "Context"},
            defaults={"name": "Default"},
        )

        assert result.rendered == "Context"
        assert "name" in result.variables_used


class TestMissingVariables:
    """Tests for missing variable handling."""

    def test_strict_mode_raises(self):
        """Test that strict mode raises on missing variable."""
        engine = TemplateEngine(strict=True)

        with pytest.raises(VariableNotFoundError) as exc_info:
            engine.render("{{missing}}", {})

        assert "missing" in str(exc_info.value)

    def test_strict_mode_shows_available(self):
        """Test that error shows available variables."""
        engine = TemplateEngine(strict=True)

        with pytest.raises(VariableNotFoundError) as exc_info:
            engine.render("{{missing}}", {"name": "test", "value": 123})

        assert "name" in str(exc_info.value)
        assert "value" in str(exc_info.value)

    def test_non_strict_mode_keeps_placeholder(self):
        """Test that non-strict mode keeps the placeholder."""
        engine = TemplateEngine(strict=False)
        result = engine.render("{{missing}}", {})

        assert result.rendered == "{{missing}}"


class TestTemplateResult:
    """Tests for TemplateResult."""

    def test_result_tracks_variables(self):
        """Test that result tracks used variables."""
        engine = TemplateEngine()
        result = engine.render(
            "{{a}} {{b}} {{c|default}}",
            {"a": "A", "b": "B"},
        )

        assert "a" in result.variables_used
        assert "b" in result.variables_used
        assert "c" in result.defaults_applied

    def test_render_string_convenience(self):
        """Test render_string convenience method."""
        engine = TemplateEngine()
        rendered = engine.render_string("{{name}}", {"name": "test"})

        assert rendered == "test"
        assert isinstance(rendered, str)


class TestExtractVariables:
    """Tests for variable extraction."""

    def test_extract_variables(self):
        """Test extracting variables from template."""
        engine = TemplateEngine()
        variables = engine.extract_variables("{{a}} {{b}} {{c|default}}")

        assert "a" in variables
        assert "b" in variables
        assert "c" in variables

    def test_get_required_variables(self):
        """Test getting required variables (no defaults)."""
        engine = TemplateEngine()
        required = engine.get_required_variables(
            "{{a}} {{b|default}} {{c}}",
            defaults={"c": "value"},
        )

        assert required == ["a"]


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_render_function(self):
        """Test render() convenience function."""
        result = render("{{name}}", {"name": "test"})
        assert result == "test"

    def test_validate_function(self):
        """Test validate() convenience function."""
        variables = validate("{{a}} {{b}}")
        assert "a" in variables
        assert "b" in variables

    def test_create_engine_function(self):
        """Test create_engine() factory function."""
        engine = create_engine(strict=False, verbose=False)
        assert isinstance(engine, TemplateEngine)
        assert engine.strict is False


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_template(self):
        """Test empty template."""
        engine = TemplateEngine()
        result = engine.render("", {})
        assert result.rendered == ""

    def test_no_variables_template(self):
        """Test template with no variables."""
        engine = TemplateEngine()
        result = engine.render("Hello World", {})
        assert result.rendered == "Hello World"

    def test_whitespace_in_variable(self):
        """Test whitespace handling in variable syntax."""
        engine = TemplateEngine()
        result = engine.render("{{ name }}", {"name": "test"})
        assert result.rendered == "test"

    def test_whitespace_in_default(self):
        """Test whitespace handling in default value."""
        engine = TemplateEngine()
        result = engine.render("{{ name | default }}", {})
        assert result.rendered == "default"

    def test_numeric_values(self):
        """Test numeric variable values."""
        engine = TemplateEngine()
        result = engine.render("Count: {{count}}", {"count": 42})
        assert result.rendered == "Count: 42"

    def test_special_characters_in_value(self):
        """Test special characters in variable value."""
        engine = TemplateEngine()
        result = engine.render("{{text}}", {"text": "Hello, World! @#$%"})
        assert result.rendered == "Hello, World! @#$%"


class TestRealWorldExamples:
    """Tests using real-world template examples."""

    def test_icon_template(self):
        """Test icon series template."""
        engine = TemplateEngine()
        template = "{{style}} icon of {{subject}}, {{background}}"
        defaults = {
            "style": "flat minimal",
            "background": "transparent",
        }

        # Generate home icon
        result = engine.render(template, {"subject": "home"}, defaults)
        assert result.rendered == "flat minimal icon of home, transparent"

        # Generate settings icon
        result = engine.render(template, {"subject": "settings"}, defaults)
        assert result.rendered == "flat minimal icon of settings, transparent"

    def test_illustration_template(self):
        """Test illustration template with overrides."""
        engine = TemplateEngine()
        template = "{{style}} illustration of {{scene}}, {{mood}} mood, {{colors}}"
        defaults = {
            "style": "watercolor",
            "mood": "peaceful",
            "colors": "pastel colors",
        }

        result = engine.render(
            template,
            {"scene": "mountain landscape", "mood": "dramatic"},
            defaults,
        )

        assert "watercolor" in result.rendered
        assert "mountain landscape" in result.rendered
        assert "dramatic" in result.rendered  # Override from context
        assert "pastel colors" in result.rendered

