# Story 007: History Tracking

**Status:** Ready for Review  
**Priority:** P1  
**Epic:** MVP Phase 1  
**Estimate:** 2-3 hours

---

## Story

As a developer, I want the CLI to track generation history so I can review past iterations, understand what prompts produced which images, and potentially rollback to previous versions.

---

## Acceptance Criteria

- [x] Each generation logged to `history/` directory
- [x] History entry includes: timestamp, prompt, params, output path, model
- [x] `img history` lists recent generations
- [x] `img history <id>` shows details of specific generation
- [x] History stored as JSON for easy parsing
- [x] History survives failed generations (logs attempt)
- [x] `--output-format json|yaml|text` for history command

---

## Tasks

- [x] Create `core/history.py` module
- [x] Implement `HistoryManager` class
- [x] Define history entry schema
- [x] Implement history file writing
- [x] Create `cli/commands/history.py` command
- [x] Implement history listing
- [x] Implement history detail view
- [x] Add history recording to generation pipeline
- [x] Write unit tests for history tracking

---

## Dev Notes

- History file format: `history/{timestamp}_{id}.json`
- Consider SQLite for future if history grows large
- Include image hash/checksum for integrity verification

**History Entry Schema:**
```json
{
  "id": "20241224_143052_abc123",
  "timestamp": "2024-12-24T14:30:52Z",
  "prompt": "flat icon of home...",
  "resolved_prompt": "flat minimal icon of home, transparent",
  "model": "图片生成4.0",
  "params": {
    "width": 512,
    "height": 512
  },
  "output_path": "output/home_abc123.png",
  "status": "success",
  "duration_ms": 2340,
  "series": "app-icons",
  "item_id": "home"
}
```

---

## Testing

- [x] Unit test: history entry creation
- [x] Unit test: history file writing
- [x] Unit test: history listing
- [x] Unit test: history detail retrieval
- [x] Unit test: failed generation logging

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Created HistoryManager class for tracking generation history
- History files stored in `history/` directory as JSON
- File naming: `{timestamp}_{prompt_hash}.json`
- Each entry includes full generation context (prompt, params, model, etc.)
- Image hash (SHA256) calculated for integrity verification
- History recorded for both successful and failed generations
- Added `img history` command with listing, detail view, search, and stats
- Search supports filtering by prompt, series, status
- Statistics show total, successful, failed, duration, series count
- Integrated history recording into generation pipeline
- Added series and item_id fields to GenerationContext for series tracking
- All 24 history tests passing (179 total tests)
- Linting clean with ruff

### File List
**Created:**
- `imgcreator/core/history.py` - HistoryManager, HistoryEntry classes
- `imgcreator/cli/commands/history.py` - History command implementation
- `tests/test_history.py` - 24 unit tests for history tracking

**Modified:**
- `imgcreator/core/pipeline.py` - Added history recording, series/item_id fields
- `imgcreator/cli/main.py` - Added history command registration
- `imgcreator/cli/commands/generate.py` - Pass project_path to pipeline

### Change Log
1. Created core/history.py with HistoryManager class
2. Implemented HistoryEntry dataclass with full schema
3. Implemented history file writing to history/ directory
4. Added image hash calculation (SHA256) for integrity
5. Implemented list_entries() with reverse chronological order
6. Implemented get_entry() for retrieving specific entries
7. Implemented search() with filtering by prompt, series, status
8. Implemented get_stats() for history statistics
9. Created cli/commands/history.py with full command
10. Added --limit, --series, --status, --search, --stats options
11. Added --output-format (text/json/yaml) support
12. Integrated history recording into pipeline.run()
13. Added series and item_id fields to GenerationContext
14. History recorded for both success and failure cases
15. Wrote 24 comprehensive unit tests
16. Fixed linting issues (imports, line length, unused variables)
