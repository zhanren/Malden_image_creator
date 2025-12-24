"""Template engine for imgcreator.

Supports Jinja2-style variable substitution:
- {{variable}} - basic variable
- {{variable|default}} - variable with default value
- {{nested.variable}} - nested variable access
"""

import re
from dataclasses import dataclass, field
from typing import Any


class TemplateError(Exception):
    """Base exception for template errors."""

    pass


class VariableNotFoundError(TemplateError):
    """Variable not found in context."""

    def __init__(self, variable: str, available: list[str] | None = None):
        self.variable = variable
        self.available = available or []
        msg = f"Variable '{{{{ {variable} }}}}' not found"
        if available:
            msg += f". Available variables: {', '.join(available)}"
        super().__init__(msg)


class TemplateSyntaxError(TemplateError):
    """Invalid template syntax."""

    pass


@dataclass
class TemplateResult:
    """Result of template rendering."""

    rendered: str
    variables_used: list[str] = field(default_factory=list)
    defaults_applied: list[str] = field(default_factory=list)


# Pattern to match {{variable}} or {{variable|default}}
# Supports: {{var}}, {{var|default}}, {{nested.var}}, {{nested.var|default value}}
VARIABLE_PATTERN = re.compile(
    r"\{\{\s*"  # Opening {{ with optional whitespace
    r"([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)"  # Variable name (with dots)
    r"(?:\s*\|\s*([^}]*))?"  # Optional |default value
    r"\s*\}\}"  # Closing }} with optional whitespace
)


def get_nested_value(data: dict[str, Any], key: str) -> Any:
    """Get a nested value from a dictionary using dot notation.

    Args:
        data: Dictionary to search
        key: Key with dot notation (e.g., "nested.value")

    Returns:
        Value at the nested key

    Raises:
        KeyError: If key not found
    """
    parts = key.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(key)
            current = current[part]
        else:
            raise KeyError(key)

    return current


def flatten_keys(data: dict[str, Any], prefix: str = "") -> list[str]:
    """Get all available keys from a nested dictionary.

    Args:
        data: Dictionary to flatten
        prefix: Current key prefix

    Returns:
        List of all available keys (with dot notation for nested)
    """
    keys = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)
        if isinstance(value, dict):
            keys.extend(flatten_keys(value, full_key))
    return keys


class TemplateEngine:
    """Template engine for variable substitution in prompts."""

    def __init__(self, strict: bool = True, verbose: bool = False):
        """Initialize the template engine.

        Args:
            strict: Raise error on missing variables (default True)
            verbose: Enable verbose logging
        """
        self.strict = strict
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[template] {message}")

    def validate(self, template: str) -> list[str]:
        """Validate template syntax and return list of variables.

        Args:
            template: Template string to validate

        Returns:
            List of variable names found in template

        Raises:
            TemplateSyntaxError: If template has invalid syntax
        """
        # Check for unbalanced braces
        open_count = template.count("{{")
        close_count = template.count("}}")

        if open_count != close_count:
            raise TemplateSyntaxError(
                f"Unbalanced braces: {open_count} '{{{{' and {close_count} '}}}}'"
            )

        # Check for nested braces (not supported)
        if "{{{{" in template or "}}}}" in template:
            raise TemplateSyntaxError("Nested braces are not supported")

        # Extract all variables
        variables = []
        for match in VARIABLE_PATTERN.finditer(template):
            var_name = match.group(1)
            if var_name not in variables:
                variables.append(var_name)

        self._log(f"Found variables: {variables}")
        return variables

    def render(
        self,
        template: str,
        context: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> TemplateResult:
        """Render a template with the given context.

        Args:
            template: Template string with {{variable}} placeholders
            context: Dictionary of variable values
            defaults: Optional dictionary of default values

        Returns:
            TemplateResult with rendered string and metadata

        Raises:
            VariableNotFoundError: If strict mode and variable not found
            TemplateSyntaxError: If template has invalid syntax
        """
        # Validate first
        self.validate(template)

        defaults = defaults or {}
        variables_used = []
        defaults_applied = []

        def replace_variable(match: re.Match) -> str:
            var_name = match.group(1)
            inline_default = match.group(2)

            self._log(f"Processing variable: {var_name}")

            # Try to get value from context
            try:
                value = get_nested_value(context, var_name)
                variables_used.append(var_name)
                self._log(f"  Resolved from context: {value}")
                return str(value)
            except KeyError:
                pass

            # Try to get value from defaults dict
            try:
                value = get_nested_value(defaults, var_name)
                defaults_applied.append(var_name)
                self._log(f"  Resolved from defaults dict: {value}")
                return str(value)
            except KeyError:
                pass

            # Try inline default value
            if inline_default is not None:
                defaults_applied.append(var_name)
                inline_default = inline_default.strip()
                self._log(f"  Using inline default: {inline_default}")
                return inline_default

            # Variable not found
            if self.strict:
                available = flatten_keys(context) + flatten_keys(defaults)
                raise VariableNotFoundError(var_name, available)

            # In non-strict mode, leave the variable as-is
            self._log("  Variable not found, keeping placeholder")
            return match.group(0)

        rendered = VARIABLE_PATTERN.sub(replace_variable, template)

        self._log(f"Rendered: {rendered}")

        return TemplateResult(
            rendered=rendered,
            variables_used=variables_used,
            defaults_applied=defaults_applied,
        )

    def render_string(
        self,
        template: str,
        context: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> str:
        """Render a template and return just the string.

        Convenience method that returns only the rendered string.

        Args:
            template: Template string
            context: Variable values
            defaults: Default values

        Returns:
            Rendered string
        """
        return self.render(template, context, defaults).rendered

    def extract_variables(self, template: str) -> list[str]:
        """Extract all variable names from a template.

        Args:
            template: Template string

        Returns:
            List of variable names (without defaults)
        """
        return self.validate(template)

    def get_required_variables(
        self,
        template: str,
        defaults: dict[str, Any] | None = None,
    ) -> list[str]:
        """Get variables that must be provided (no default available).

        Args:
            template: Template string
            defaults: Available defaults

        Returns:
            List of required variable names
        """
        defaults = defaults or {}
        required = []

        for match in VARIABLE_PATTERN.finditer(template):
            var_name = match.group(1)
            inline_default = match.group(2)

            # Has inline default?
            if inline_default is not None:
                continue

            # Has default in defaults dict?
            try:
                get_nested_value(defaults, var_name)
                continue
            except KeyError:
                pass

            if var_name not in required:
                required.append(var_name)

        return required


def create_engine(strict: bool = True, verbose: bool = False) -> TemplateEngine:
    """Create a template engine.

    Args:
        strict: Raise error on missing variables
        verbose: Enable verbose logging

    Returns:
        Configured TemplateEngine
    """
    return TemplateEngine(strict=strict, verbose=verbose)


# Convenience functions
def render(
    template: str,
    context: dict[str, Any],
    defaults: dict[str, Any] | None = None,
    strict: bool = True,
) -> str:
    """Render a template string.

    Args:
        template: Template with {{variable}} placeholders
        context: Variable values
        defaults: Default values
        strict: Raise error on missing variables

    Returns:
        Rendered string
    """
    engine = TemplateEngine(strict=strict)
    return engine.render_string(template, context, defaults)


def validate(template: str) -> list[str]:
    """Validate a template and return variables.

    Args:
        template: Template string

    Returns:
        List of variable names

    Raises:
        TemplateSyntaxError: If invalid
    """
    engine = TemplateEngine()
    return engine.validate(template)

