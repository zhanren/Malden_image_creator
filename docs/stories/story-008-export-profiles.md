# Story 008: Export Profiles

**Status:** Ready for Review  
**Priority:** P1  
**Epic:** MVP Phase 1  
**Estimate:** 3-4 hours

---

## Story

As a mobile developer, I want to export generated images to multiple sizes (iOS @1x/@2x/@3x, Android density buckets, custom dimensions) so I can directly use them as app assets.

---

## Acceptance Criteria

- [x] `img export` processes images in output directory
- [x] `img export --profile ios` generates @1x, @2x, @3x variants
- [x] `img export --profile android` generates mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi
- [x] `img export --size 100x100` generates specific size
- [x] `img export --all` applies all configured profiles
- [x] Maintains aspect ratio (optional flag to force exact size)
- [x] Preserves transparency (PNG)
- [x] Creates organized directory structure per profile
- [x] `--dry-run` shows what would be exported
- [x] Completion time < 10 seconds for typical batch

---

## Tasks

- [x] Create `export/profiles.py` with profile definitions
- [x] Create `export/resize.py` with image resizing logic
- [x] Create `cli/commands/export.py` command
- [x] Implement iOS profile (@1x, @2x, @3x)
- [x] Implement Android profile (density buckets)
- [x] Implement custom size export
- [x] Implement directory organization
- [x] Add dry-run mode
- [x] Add progress indicator
- [x] Write unit tests for export functionality

---

## Dev Notes

- Use Pillow for image resizing
- Use LANCZOS resampling for quality
- Consider parallel processing for large batches

**Profile Definitions:**
```python
IOS_PROFILE = {
    "@1x": 1.0,
    "@2x": 2.0,
    "@3x": 3.0
}

ANDROID_PROFILE = {
    "mdpi": 1.0,
    "hdpi": 1.5,
    "xhdpi": 2.0,
    "xxhdpi": 3.0,
    "xxxhdpi": 4.0
}
```

**Output Structure:**
```
export/
├── ios/
│   ├── home@1x.png
│   ├── home@2x.png
│   └── home@3x.png
├── android/
│   ├── mdpi/home.png
│   ├── hdpi/home.png
│   └── ...
└── custom/
    └── home_100x100.png
```

---

## Testing

- [x] Unit test: iOS profile generation
- [x] Unit test: Android profile generation
- [x] Unit test: custom size generation
- [x] Unit test: aspect ratio preservation
- [x] Unit test: transparency preservation
- [x] Integration test: full export workflow

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None - implementation completed without debugging issues.

### Completion Notes
- Created export/profiles.py with iOS and Android profile definitions
- Implemented export/resize.py with Pillow-based image resizing
- Uses LANCZOS resampling for high-quality resizing
- iOS export creates @1x, @2x, @3x variants in ios/ directory
- Android export creates density buckets in android/{density}/ directories
- Custom size export supports WIDTHxHEIGHT format
- Aspect ratio preservation by default (can be disabled with --no-maintain-aspect)
- Transparency (RGBA) fully preserved in all exports
- Progress bar shows export progress for batch operations
- Dry-run mode shows preview of what would be exported
- Defaults to processing all PNG/JPG files in output/ directory
- All 26 export tests passing (205 total tests)
- Linting clean with ruff

### File List
**Created:**
- `imgcreator/export/profiles.py` - Profile definitions (iOS, Android, custom)
- `imgcreator/export/resize.py` - Image resizing and export functions
- `imgcreator/cli/commands/export.py` - Export command implementation
- `tests/test_export.py` - 26 unit tests for export functionality

**Modified:**
- `imgcreator/cli/main.py` - Added export command registration

### Change Log
1. Created export/profiles.py with IOS_PROFILE and ANDROID_PROFILE
2. Implemented ScaleProfile and SizeProfile dataclasses
3. Added parse_custom_size() for WIDTHxHEIGHT parsing
4. Created export/resize.py with image loading and resizing functions
5. Implemented resize_with_scale() for scale-based resizing
6. Implemented resize_to_size() with aspect ratio preservation
7. Implemented export_ios() for iOS @1x/@2x/@3x variants
8. Implemented export_android() for Android density buckets
9. Implemented export_custom_size() for arbitrary dimensions
10. Created export_image() unified export function
11. Created cli/commands/export.py with full export command
12. Added --profile, --size, --all options
13. Added --maintain-aspect/--no-maintain-aspect flag
14. Added --dry-run mode with preview
15. Added progress bar for batch exports
16. Defaults to processing output/ directory if no images specified
17. Wrote 26 comprehensive unit tests
18. Fixed linting issues (unused imports, duplicate keys, line length)
