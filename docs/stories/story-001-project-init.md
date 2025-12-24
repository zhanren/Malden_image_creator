# Story 001: Project Init Command

**Status:** Ready for Review  
**Priority:** P0  
**Epic:** MVP Phase 1  
**Estimate:** 2-3 hours

---

## Story

As a mobile app developer, I want to run `img init` to create a new image project with proper directory structure and configuration files, so I can quickly start generating themed image assets.

---

## Acceptance Criteria

- [x] `img init` creates project directory structure
- [x] `img init <name>` creates named project folder
- [x] `img init` in existing project warns and prompts for confirmation
- [x] Creates `imgcreator.yaml` with default global config
- [x] Creates `series/` directory for series definitions
- [x] Creates `output/` directory for generated images
- [x] Creates `history/` directory for iteration tracking
- [x] Creates `.env.example` with `VOLCENGINE_API_KEY` placeholder
- [x] Displays success message with next steps
- [x] `--help` flag shows usage information

---

## Tasks

- [x] Set up Python project structure with Click CLI framework
- [x] Create `cli/main.py` entry point with Click group
- [x] Implement `cli/commands/init.py` with init command
- [x] Create default `imgcreator.yaml` template content
- [x] Implement directory creation logic
- [x] Add existing project detection and warning
- [x] Add success message with usage hints
- [x] Write unit tests for init command

---

## Dev Notes

- Use Click for CLI framework (per PRD tech stack)
- Follow directory structure from PRD section 4.4
- Default config should include commented examples
- Consider `--force` flag for overwriting existing projects

---

## Testing

- [x] Unit test: directory creation
- [x] Unit test: config file generation
- [x] Unit test: existing project detection
- [x] Integration test: full init workflow

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Implemented using Click CLI framework as specified in PRD
- Added `--force` flag for reinitializing existing projects
- Created comprehensive default config with comments and examples
- Added `.gitignore` to exclude generated files and .env
- All 14 unit tests passing
- Linting clean with ruff

### File List
**Created:**
- `pyproject.toml` - Python project configuration with dependencies
- `requirements.txt` - Dependency list for pip
- `imgcreator/__init__.py` - Package init with version
- `imgcreator/cli/__init__.py` - CLI module init
- `imgcreator/cli/main.py` - CLI entry point with Click group
- `imgcreator/cli/commands/__init__.py` - Commands module init
- `imgcreator/cli/commands/init.py` - Init command implementation
- `imgcreator/core/__init__.py` - Core module init (placeholder)
- `imgcreator/api/__init__.py` - API module init (placeholder)
- `imgcreator/export/__init__.py` - Export module init (placeholder)
- `imgcreator/utils/__init__.py` - Utils module init (placeholder)
- `tests/__init__.py` - Tests module init
- `tests/test_init.py` - Unit tests for init command

### Change Log
1. Created Python project structure with pyproject.toml and requirements.txt
2. Set up imgcreator package with CLI, core, api, export, utils modules
3. Implemented cli/main.py with Click group and version option
4. Implemented cli/commands/init.py with full init command functionality
5. Added default imgcreator.yaml template with comprehensive examples
6. Added .env.example template for API key configuration
7. Added .gitignore generation for output/history directories
8. Added existing project detection with user confirmation prompt
9. Added --force flag to skip confirmation
10. Added verbose mode showing created files
11. Wrote 14 unit tests covering all acceptance criteria
12. Fixed linting issues (removed unused imports, fixed line length)
