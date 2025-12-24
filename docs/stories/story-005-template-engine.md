# Story 005: Template Engine

**Status:** Ready for Review  
**Priority:** P0  
**Epic:** MVP Phase 1  
**Estimate:** 2-3 hours

---

## Story

As a developer, I want to use variable placeholders in my prompts so I can create reusable templates for generating series of related images.

---

## Acceptance Criteria

- [x] Supports `{{variable}}` syntax in prompts
- [x] Variables resolve from series item definitions
- [x] Variables can have default values: `{{variable|default}}`
- [x] Unresolved variables produce clear error messages
- [x] Supports nested variable references
- [x] Template validation before generation
- [x] `--verbose` shows resolved prompt

---

## Tasks

- [x] Create `core/template.py` module
- [x] Implement `TemplateEngine` class
- [x] Implement variable substitution logic
- [x] Add default value support
- [x] Add template validation
- [x] Add helpful error messages for missing variables
- [x] Integrate with generate command
- [x] Write unit tests for template engine

---

## Dev Notes

- Use Jinja2-style syntax but keep it simple
- Could use actual Jinja2 or implement lightweight custom parser
- Variables come from series item context

**Template Example:**
```yaml
# series/icons.yaml
template: "{{style}} icon of {{subject}}, {{background}}"
defaults:
  style: "flat minimal"
  background: "transparent"
items:
  - subject: "home"
  - subject: "settings"
  - subject: "user profile"
```

**Resolved Prompts:**
- "flat minimal icon of home, transparent"
- "flat minimal icon of settings, transparent"
- "flat minimal icon of user profile, transparent"

---

## Testing

- [x] Unit test: basic variable substitution
- [x] Unit test: default values
- [x] Unit test: missing variable error
- [x] Unit test: nested variables
- [x] Unit test: template validation

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Implemented lightweight Jinja2-style template engine (no Jinja2 dependency)
- Supports `{{variable}}` and `{{variable|default}}` syntax
- Supports nested variable access with dot notation: `{{user.name}}`
- Strict mode (default) raises VariableNotFoundError with available variables list
- Non-strict mode keeps unresolved placeholders as-is
- Template validation catches unbalanced braces
- Integrated with GenerationContext for template-based prompt resolution
- All 40 template tests passing (130 total tests)
- Linting clean with ruff

### File List
**Created:**
- `imgcreator/core/template.py` - TemplateEngine class, validation, substitution
- `tests/test_template.py` - 40 unit tests for template engine

**Modified:**
- `imgcreator/core/pipeline.py` - Added template_context and template_defaults to GenerationContext

### Change Log
1. Created core/template.py with TemplateEngine class
2. Implemented regex-based variable pattern matching
3. Implemented variable substitution with context lookup
4. Added inline default value support (`{{var|default}}`)
5. Added defaults dictionary support
6. Added nested variable access with dot notation
7. Implemented template validation (unbalanced braces detection)
8. Added VariableNotFoundError with available variables hint
9. Added strict/non-strict modes
10. Created convenience functions (render, validate)
11. Integrated template engine with GenerationContext
12. Wrote 40 comprehensive unit tests
13. Fixed linting issues (f-string without placeholders)
