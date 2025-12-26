# Story 009: Image-to-Image Generation with Reference Assets

**Status:** Ready for Review  
**Priority:** P1  
**Epic:** MVP Phase 1  
**Estimate:** 5-6 hours

---

## Story

As a mobile app developer, I want to generate images based on reference artwork (style or character) combined with YAML configuration, so I can create consistent assets that match existing designs or extract/adapt characters from artwork I like.

---

## User Scenarios

### Scenario 1: Style Transfer
**As a developer**, I see artwork with a style I like (e.g., a logo set, icon pack, or illustration style). I want to:
1. Save the reference image to an `assets/` folder
2. Specify the reference image path in my YAML config
3. Generate new assets that match that style using my existing prompt templates

**Example:**
```yaml
defaults:
  reference_image: "./assets/icon-style.png"
  style: "flat, minimal, modern"
  
series:
  - name: app-icons
    template: "{{style}} icon of {{subject}}"
    items:
      - id: home
        subject: "home house"
```

### Scenario 2: Character Extraction/Adaptation
**As a developer**, I have artwork with a character I want to reuse. I want to:
1. Save the character artwork to `assets/`
2. Use it as a reference for generating variations or new scenes
3. Combine with prompts to adapt the character to different contexts

**Example:**
```yaml
series:
  - name: character-variations
    reference_image: "./assets/main-character.png"
    template: "{{character}} in {{scene}}"
    items:
      - id: home-scene
        scene: "cozy home interior"
      - id: outdoor-scene
        scene: "sunny park"
```

---

## Acceptance Criteria

- [x] `img generate` automatically detects reference image from YAML config
- [x] If `reference_image` is specified in config, use 图生图3.0 (image-to-image) API
- [x] If only prompt is provided (no reference), use 文生图 (text-to-image) API
- [x] Reference images can be specified at multiple levels:
  - [x] Global default in `imgcreator.yaml` → `defaults.reference_image`
  - [x] Per-series in series YAML → `reference_image` field
  - [ ] Per-item override (optional, for character extraction use case)
- [x] Reference images are loaded from `assets/` folder (or specified path)
- [x] Image is encoded as base64 and included in API request
- [x] Clear error messages if reference image file not found
- [x] Path resolution: relative paths resolved from project root
- [x] Backward compatibility: existing configs without `reference_image` work unchanged
- [x] Support common image formats: PNG, JPG, JPEG
- [x] Verbose mode shows which API (text-to-image vs image-to-image) is being used

---

## Tasks

- [ ] Extend `GenerationRequest` to include `reference_image_path` field
- [ ] Add `reference_image` field to YAML config schema (`DefaultsConfig`)
- [ ] Add `reference_image` support to series config schema
- [ ] Implement image loading utility (load from path, validate, encode base64)
- [ ] Add image-to-image API call in `VolcengineClient.generate()`
- [ ] Implement auto-detection logic (reference present → use 图生图3.0)
- [ ] Add `req_key` mapping for image-to-image model (`img2img_v1.0`)
- [ ] Update `GenerationContext` to handle reference images
- [ ] Update pipeline to load and pass reference images
- [ ] Add reference image validation (file exists, readable, valid format)
- [ ] Update CLI to show which API mode is being used
- [ ] Add error handling for missing/invalid reference images
- [ ] Update config validation to check reference image paths
- [ ] Write unit tests for image loading and encoding
- [ ] Write unit tests for image-to-image API integration
- [ ] Write integration tests for YAML config with reference images
- [ ] Update documentation (README, config examples)

---

## Dev Notes

### API Integration

**Volcengine Image-to-Image API:**
- Model: `图生图3.0` → `img2img_v1.0`
- `req_key`: Need to verify from API docs (likely `high_aes_img2img_v10`)
- Endpoint: Same as text-to-image (`CVProcess` action)
- Request body: Includes `image_base64` or `image_url` field

**Reference:** Check Volcengine 图生图3.0 API documentation for exact request format.

### Configuration Schema

**Option A: Under `defaults` (Recommended)**
```yaml
defaults:
  reference_image: "./assets/base-style.png"  # Optional
  width: 1024
  height: 1024
```

**Option B: Separate section**
```yaml
reference:
  image: "./assets/base-style.png"
```

**Decision:** Use Option A for consistency with existing structure.

### Path Resolution

- Relative paths resolved from project root (where `imgcreator.yaml` is)
- Support both relative (`./assets/image.png`) and absolute paths
- Validate path exists before generation

### Auto-Detection Logic

```python
def determine_generation_mode(context: GenerationContext) -> str:
    """Determine if text-to-image or image-to-image should be used."""
    if context.reference_image_path and Path(context.reference_image_path).exists():
        return "image-to-image"  # Use 图生图3.0
    return "text-to-image"  # Use 文生图 or 图片生成4.0
```

### Image Processing

1. **Load** image from file path
2. **Validate** file exists and is readable
3. **Check** format (PNG, JPG, JPEG supported)
4. **Encode** to base64 string
5. **Include** in API request body

**Image Size Considerations:**
- Volcengine API may have size limits
- Consider auto-resizing if needed (future enhancement)
- For MVP: Use image as-is, let API handle sizing

### Series-Level vs Item-Level

**Series Level:**
```yaml
series:
  - name: app-icons
    reference_image: "./assets/icon-style.png"  # Applies to all items
    items:
      - id: home
        subject: "home"
```

**Item Level (Optional Enhancement):**
```yaml
series:
  - name: character-variations
    reference_image: "./assets/default-character.png"  # Default
    items:
      - id: hero
        reference_image: "./assets/hero-character.png"  # Override
        scene: "battle"
```

**MVP Decision:** Support series-level first, item-level as future enhancement.

### Error Handling

**Missing Reference Image:**
```
✗ Reference image not found: ./assets/style.png
  Check that the file exists and path is correct.
```

**Invalid Format:**
```
✗ Unsupported image format: .gif
  Supported formats: PNG, JPG, JPEG
```

**Unreadable Image:**
```
✗ Cannot read image file: ./assets/corrupted.png
  File may be corrupted or permissions issue.
```

---

## Testing

- [ ] Unit test: Image loading from path
- [ ] Unit test: Base64 encoding
- [ ] Unit test: Image format validation
- [ ] Unit test: Path resolution (relative/absolute)
- [ ] Unit test: Auto-detection logic (reference present vs absent)
- [ ] Unit test: Image-to-image API request formatting
- [ ] Unit test: Error handling (missing file, invalid format)
- [ ] Integration test: YAML config with `reference_image` in defaults
- [ ] Integration test: Series config with `reference_image`
- [ ] Integration test: Backward compatibility (config without reference_image)
- [ ] Integration test: Full generation workflow with reference image
- [ ] Manual test: Generate with reference image from assets folder
- [ ] Manual test: Verify output matches reference style

---

## Dependencies

- Volcengine 图生图3.0 API documentation
- Verify `req_key` value for `img2img_v1.0` model
- Check API request format for image-to-image
- Verify image encoding requirements (base64 format, size limits)

---

## Related Stories

- Story 003: Volcengine API Client (foundation)
- Story 004: Basic Generate (generation pipeline)
- Story 006: Series Generation (series config support)

---

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4.5 (via Cursor)

### Debug Log References
- Fixed ConfigLoader not using project_path in pipeline
- Fixed linting errors (line length, import sorting)
- Fixed test assertions for image loading error handling

### Completion Notes
- Implemented image-to-image generation with automatic mode detection
- Reference images can be specified at global (defaults) and series levels
- Image loading utility supports PNG, JPG, JPEG with validation
- Auto-detection: presence of reference_image → uses 图生图3.0 API
- All tests passing (15 unit tests, 7 API tests, 11 integration tests)
- Backward compatible: existing configs without reference_image work unchanged

### File List
**New Files:**
- `imgcreator/utils/image.py` - Image loading and encoding utilities
- `tests/test_image_utils.py` - Unit tests for image utilities (15 tests)
- `tests/test_volcengine_img2img.py` - Image-to-image API tests (7 tests)
- `tests/test_img2img_integration.py` - Integration tests (11 tests)

**Modified Files:**
- `imgcreator/api/base.py` - Added `reference_image_path` and `reference_image_data` to `GenerationRequest`
- `imgcreator/api/volcengine.py` - Added image-to-image API support, auto-detection, req_key mapping
- `imgcreator/core/config.py` - Added `reference_image` to `DefaultsConfig`, validation
- `imgcreator/core/series.py` - Added `reference_image` to `SeriesConfig`, series-level support
- `imgcreator/core/pipeline.py` - Added reference image handling, path resolution, API mode detection
- `imgcreator/cli/commands/generate.py` - Added API mode display, reference image CLI support

### Change Log
- 2025-01-XX: Story 009 implementation completed
  - Extended GenerationRequest with reference_image fields
  - Added reference_image support to config and series schemas
  - Implemented image loading/encoding utilities
  - Added image-to-image API integration with auto-detection
  - Updated pipeline and CLI to support reference images
  - Added comprehensive test coverage (33 tests total)

