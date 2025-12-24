# Story 004: Basic Generate Command

**Status:** Ready for Review  
**Priority:** P0  
**Epic:** MVP Phase 1  
**Estimate:** 3-4 hours

---

## Story

As a developer, I want to run `img generate` to create a single image from a prompt defined in my config, so I can quickly test and iterate on image generation.

---

## Acceptance Criteria

- [x] `img generate` reads prompt from project config
- [x] `img generate --prompt "..."` uses inline prompt
- [x] `img generate --sample` generates single sample image
- [x] Saves generated image to `output/` directory
- [x] Displays generation time and output path
- [x] `--dry-run` shows what would generate without API call
- [x] `--output-format json|yaml|text` controls output format
- [x] `--verbose` shows detailed API call info
- [x] Returns non-zero exit code on failure

---

## Tasks

- [x] Create `cli/commands/generate.py` with generate command
- [x] Implement prompt resolution (config vs inline)
- [x] Create `core/pipeline.py` for generation orchestration
- [x] Implement image saving with proper naming
- [x] Add dry-run mode
- [x] Add output format options
- [x] Add verbose logging
- [x] Wire up API client integration
- [x] Write unit tests for generate command

---

## Dev Notes

- Depends on: Story 002 (Config), Story 003 (API Client)
- Output filename format: `{timestamp}_{prompt_hash}.png`
- Dry-run should show resolved prompt, model, dimensions
- Consider progress indicator for long API calls

**Command Examples:**
```bash
img generate                    # Use config prompt
img generate --prompt "cat"     # Inline prompt
img generate --sample           # Single sample mode
img generate --dry-run          # Preview only
img generate -v                 # Verbose output
```

---

## Testing

- [x] Unit test: prompt resolution logic
- [x] Unit test: dry-run output
- [x] Unit test: output format options
- [x] Integration test: full generation pipeline (mocked API)

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Created GenerationPipeline class for orchestrating generation
- Implemented GenerationContext for holding resolved parameters
- Style prefix merging with prompt (style + prompt)
- Filename format: {timestamp}_{prompt_hash}.png using MD5 hash
- Dry-run mode shows full preview without API call
- Output formats: text (human-readable), json, yaml
- Full integration with ConfigLoader and VolcengineClient
- All 23 generate tests passing (90 total tests)
- Linting clean with ruff

### File List
**Created:**
- `imgcreator/core/pipeline.py` - GenerationPipeline, GenerationContext, PipelineResult
- `imgcreator/cli/commands/generate.py` - Generate command implementation
- `tests/test_generate.py` - 23 unit tests for generate command

**Modified:**
- `imgcreator/cli/main.py` - Added generate command registration

### Change Log
1. Created core/pipeline.py with GenerationPipeline class
2. Implemented GenerationContext dataclass for generation parameters
3. Implemented PipelineResult dataclass for results
4. Added generate_filename() with timestamp + MD5 hash
5. Implemented prompt resolution with style prefix
6. Created cli/commands/generate.py with Click command
7. Added --prompt, --width, --height, --model, --style, --seed options
8. Added --sample flag for single sample mode
9. Added --dry-run mode with full preview
10. Added --output-format (text/json/yaml) option
11. Integrated with ConfigLoader and VolcengineClient
12. Added proper error handling with exit codes
13. Wrote 23 comprehensive unit tests
14. Fixed linting issues (unused imports)
