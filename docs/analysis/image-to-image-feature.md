# Feature Analysis: Image-to-Image Generation with YAML + Assets

**Date:** 2024-12-25  
**Analyst:** Mary (Business Analyst)  
**Status:** Requirements Gathering

---

## Executive Summary

Add support for image-to-image generation where users can provide reference assets (images) alongside YAML configuration to generate similar styled assets or extract/adapt characters from existing artwork.

---

## User Scenarios

### Scenario 1: Style Transfer
**User Story:** "I see artwork I like and want to create similar assets in that style"

**Example:**
- User finds a logo/icon set with a specific art style
- Wants to generate new icons matching that style
- Uses reference image + YAML config to maintain consistency

### Scenario 2: Character Extraction/Adaptation
**User Story:** "I want to use a character from existing art in new contexts"

**Example:**
- User has artwork with a character they like
- Wants to generate variations or use character in different scenes
- Uses reference image + prompt to guide generation

---

## Requirements

### Functional Requirements

1. **YAML Configuration Support**
   - Reference image path specified in YAML config
   - Support at multiple levels:
     - Global config (default reference)
     - Project config (project-wide reference)
     - Series config (per-series reference)
     - Per-item config (individual item reference)

2. **Asset Management**
   - Store reference images in a specific folder (e.g., `assets/` or `references/`)
   - Support multiple image formats (PNG, JPG, etc.)
   - Validate image exists before generation

3. **API Routing Logic**
   - **Text-only prompt** → Use 文生图 (text-to-image) API
   - **Reference asset provided** → Use 图生图 (image-to-image) API
   - Automatic detection based on config/CLI parameters

4. **Image Upload/Encoding**
   - Encode reference image as base64 for API
   - Handle image preprocessing if needed (resize, format conversion)
   - Support image URL or local file path

### Technical Requirements

1. **API Integration**
   - Implement 图生图3.0 (img2img_v1.0) endpoint
   - Use appropriate `req_key` for image-to-image model
   - Handle image encoding and request formatting

2. **Configuration Schema**
   - Extend YAML schema to include `reference_image` field
   - Support path resolution (relative to project root)
   - Maintain backward compatibility (existing configs still work)

3. **CLI Interface**
   - Optional: `--reference-image PATH` flag for CLI override
   - Automatic detection from YAML config
   - Clear error messages if reference image not found

---

## Design Considerations

### 1. YAML Configuration Structure

**Option A: Top-level reference**
```yaml
api:
  provider: volcengine
  model: "图生图3.0"  # Auto-select when reference_image present

defaults:
  reference_image: "./assets/base-style.png"  # Global default
  width: 1024
  height: 1024
```

**Option B: Separate reference section**
```yaml
reference:
  image: "./assets/base-style.png"
  strength: 0.7  # How much to follow reference (future enhancement)
```

**Option C: Per-series/item reference**
```yaml
series:
  - name: app-icons
    reference_image: "./assets/icon-style.png"
    items:
      - id: home
        reference_image: "./assets/home-reference.png"  # Override
```

### 2. Asset Folder Structure

**Proposed:**
```
project/
├── assets/          # Reference images
│   ├── styles/
│   ├── characters/
│   └── references/
├── imgcreator.yaml
└── series/
```

### 3. API Model Selection Logic

```python
if reference_image_path:
    model = "图生图3.0"  # img2img_v1.0
    req_key = "high_aes_img2img_v10"
else:
    model = config.api.model or "图片生成4.0"  # Default text-to-image
    req_key = "high_aes_general_v20"
```

### 4. Image Processing Pipeline

1. **Load** reference image from path
2. **Validate** image exists and is readable
3. **Preprocess** (optional: resize to match target dimensions)
4. **Encode** to base64
5. **Include** in API request body

---

## Implementation Questions

### Open Questions

1. **Image Strength/Influence**
   - Should there be a parameter to control how much the reference influences output?
   - Volcengine API may support this - need to check docs

2. **Multiple Reference Images**
   - Support multiple reference images?
   - Or single reference only (MVP)?

3. **Image Preprocessing**
   - Auto-resize to match target dimensions?
   - Maintain aspect ratio?
   - Format conversion requirements?

4. **Error Handling**
   - What if reference image is too large?
   - What if format is unsupported?
   - What if reference image is corrupted?

5. **CLI vs YAML Priority**
   - If both `--reference-image` flag and YAML config have reference, which takes precedence?
   - Suggested: CLI flag overrides YAML

6. **Series Generation**
   - Can a series use one reference image for all items?
   - Or per-item references?
   - Or both (series default + item override)?

---

## Proposed Implementation Plan

### Phase 1: Core Functionality (MVP)
1. ✅ Extend `GenerationRequest` to include `reference_image_path`
2. ✅ Add `reference_image` field to YAML config schema
3. ✅ Implement image loading and base64 encoding
4. ✅ Add image-to-image API call in VolcengineClient
5. ✅ Auto-detect model based on reference image presence

### Phase 2: Enhanced Features
1. Support multiple reference images
2. Image strength/influence parameter
3. Image preprocessing (auto-resize, format conversion)
4. Reference image validation and error handling
5. CLI `--reference-image` flag

### Phase 3: Advanced Features
1. Per-series and per-item reference images
2. Reference image caching/optimization
3. Style extraction and analysis
4. Batch processing with references

---

## Next Steps

1. **Review Volcengine API Documentation**
   - Check 图生图3.0 API requirements
   - Verify request format for image-to-image
   - Confirm req_key and model_version values

2. **Design Decision: YAML Structure**
   - Choose between Option A, B, or C above
   - Consider backward compatibility

3. **Create User Story**
   - Document as a new story for PM/DEV team
   - Define acceptance criteria

4. **Technical Spike**
   - Test image-to-image API call
   - Verify image encoding format
   - Test with sample reference image

---

## Risks & Considerations

1. **API Limitations**
   - Volcengine image-to-image API may have different rate limits
   - Image size/format restrictions
   - Cost implications (may be different pricing)

2. **User Experience**
   - Need clear documentation on when to use text vs image-to-image
   - Error messages should guide users if reference image issues occur

3. **Backward Compatibility**
   - Existing YAML configs must continue to work
   - Default behavior (text-to-image) should remain unchanged

---

## Recommendations

1. **Start with MVP**: Single reference image, YAML config only
2. **Auto-detection**: Automatically use image-to-image when reference provided
3. **Clear folder structure**: Use `assets/` folder for reference images
4. **Comprehensive error handling**: Validate images early with helpful messages
5. **Documentation**: Clear examples showing text-to-image vs image-to-image usage

---

**Status:** Ready for technical design and implementation planning

