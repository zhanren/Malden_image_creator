# Story 006: Series Generation

**Status:** Ready for Review  
**Priority:** P1  
**Epic:** MVP Phase 1  
**Estimate:** 3-4 hours

---

## Story

As a developer, I want to run `img generate --series` to batch generate all images defined in a series.yaml file, so I can create consistent icon sets efficiently.

---

## Acceptance Criteria

- [x] `img generate --series <name>` generates all items in series
- [x] `img generate --series` uses default series if only one exists
- [x] Series definition in YAML with template and items
- [x] Each item inherits series defaults
- [x] Progress indicator shows batch progress
- [x] Continues on individual failures (logs errors)
- [x] Summary report at completion
- [x] `--dry-run` shows all resolved prompts
- [x] Respects rate limits between API calls

---

## Tasks

- [x] Create series YAML schema definition
- [x] Implement series file loading and parsing
- [x] Implement batch generation loop
- [x] Add progress indicator (click.progressbar)
- [x] Add error handling with continue-on-failure
- [x] Add completion summary report
- [x] Add rate limit delay between requests
- [x] Integrate with template engine
- [x] Write unit tests for series generation

---

## Dev Notes

- Depends on: Story 004 (Generate), Story 005 (Template)
- Consider parallel generation (future enhancement)
- Add `--limit N` to generate only first N items (for testing)

**Series Definition Example:**
```yaml
# series/app-icons.yaml
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
```

---

## Testing

- [x] Unit test: series file parsing
- [x] Unit test: item iteration
- [x] Unit test: error handling (continue on failure)
- [x] Unit test: dry-run all items
- [x] Integration test: batch generation (mocked API)

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Created SeriesLoader class for loading and validating series YAML files
- Series files stored in `series/` directory with `.yaml` or `.yml` extension
- Series definition includes: name, template, defaults, config (overrides), items
- Each item has an `id` and optional data fields for template variables
- Batch generation uses click.progressbar for visual progress
- Error handling continues on individual failures, collects errors for summary
- Rate limiting: 0.5s delay between API calls
- Summary report shows total, success, failed counts and duration
- Dry-run mode shows all resolved prompts without API calls
- `--limit N` option for testing with subset of items
- All 25 series tests passing (155 total tests)
- Linting clean with ruff

### File List
**Created:**
- `imgcreator/core/series.py` - SeriesLoader, Series, SeriesItem, SeriesConfig classes
- `tests/test_series.py` - 25 unit tests for series loading and validation

**Modified:**
- `imgcreator/cli/commands/generate.py` - Added --series option and batch generation logic

### Change Log
1. Created core/series.py with SeriesLoader and data classes
2. Implemented YAML series file loading with validation
3. Added support for .yaml and .yml extensions
4. Implemented default series detection (single series only)
5. Added SeriesConfig for per-series config overrides
6. Integrated series generation into generate command
7. Added --series and --limit options
8. Implemented batch generation loop with progress bar
9. Added error handling with continue-on-failure
10. Added 0.5s rate limit delay between requests
11. Implemented summary report with success/failure counts
12. Added dry-run support for series (shows all resolved prompts)
13. Integrated with template engine for variable substitution
14. Wrote 25 comprehensive unit tests
15. Fixed linting issues (imports, line length)
