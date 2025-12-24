# Story 002: YAML Config System

**Status:** Ready for Review  
**Priority:** P0  
**Epic:** MVP Phase 1  
**Estimate:** 3-4 hours

---

## Story

As a developer, I want a 3-layer YAML configuration system (global → project → per-image) so I can set defaults globally while overriding specific settings for individual images.

---

## Acceptance Criteria

- [x] Load global config from `~/.imgcreator/config.yaml` (if exists)
- [x] Load project config from `./imgcreator.yaml`
- [x] Load per-image config from series definition
- [x] Config merges with proper precedence (per-image > project > global)
- [x] Validates required fields (API key presence, valid model names)
- [x] Clear error messages for invalid/missing config
- [x] Supports comments in YAML files
- [x] `--verbose` shows resolved config values

---

## Tasks

- [x] Create `core/config.py` module
- [x] Implement `ConfigLoader` class with layer loading
- [x] Implement config merge logic with proper precedence
- [x] Create config schema validation
- [x] Add helpful error messages for validation failures
- [x] Implement `--verbose` config display
- [x] Write unit tests for config loading and merging

---

## Dev Notes

- Use PyYAML for parsing
- Config schema should match PRD requirements
- Support environment variable substitution in config values (e.g., `${VOLCENGINE_API_KEY}`)
- Consider using pydantic or dataclasses for config models

**Config Structure:**
```yaml
# imgcreator.yaml
api:
  provider: volcengine
  model: "图片生成4.0"
defaults:
  width: 1024
  height: 1024
  style: "flat icon, minimal"
output:
  base_dir: ./output
```

---

## Testing

- [x] Unit test: global config loading
- [x] Unit test: project config loading
- [x] Unit test: config merge precedence
- [x] Unit test: validation errors
- [x] Unit test: env var substitution

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Implemented using dataclasses for type-safe config models
- Added environment variable substitution with `${VAR}` and `${VAR:default}` syntax
- Deep merge algorithm properly handles nested dictionaries
- Validation checks provider, model, width, height values
- Added `img config` command to display resolved configuration
- All 29 config tests passing (43 total tests)
- Linting clean with ruff

### File List
**Created:**
- `imgcreator/core/config.py` - ConfigLoader class, validation, env var substitution
- `imgcreator/cli/commands/config.py` - Config display command
- `tests/test_config.py` - 29 unit tests for config system

**Modified:**
- `imgcreator/cli/main.py` - Added config command registration

### Change Log
1. Created core/config.py with ConfigLoader class
2. Implemented 3-layer config loading (global → project → per-image)
3. Implemented deep_merge function for nested dict merging
4. Added environment variable substitution with default value support
5. Created dataclass-based config models (APIConfig, DefaultsConfig, etc.)
6. Added validation for provider, model, width, height values
7. Implemented helpful error messages with suggestions
8. Created cli/commands/config.py for config display
9. Added --verbose support showing resolved config
10. Added --validate flag for config validation only
11. Added --global flag to show global config path
12. Wrote 29 comprehensive unit tests
13. Fixed linting issues (unused imports)
