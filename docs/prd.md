# Product Requirements Document: AI Image Series Creator CLI

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** December 24, 2024  
**Author:** John (PM Agent)

---

## 1. Introduction

### 1.1 Purpose

A CLI tool that enables mobile app developers to rapidly create themed image series (icons, assets) using AI image generation, with a focus on solving the "last 10%" refinement problem through template-based workflows, golden sample iteration, and batch processing.

### 1.2 Scope

**In Scope:**
- Project initialization and YAML-based configuration
- Volcengine Jimeng AI API integration for image generation
- Template engine with variable substitution
- Series batch generation
- Golden sample workflow (refine one → apply to batch)
- Export profiles for iOS/Android asset sizes
- Configurable custom dimensions (e.g., 100x100, square, arbitrary ratios)
- History tracking and iteration management
- Developer DX: dry-run, lint, cost estimates, watch mode, verbose output

**Out of Scope:**
- GUI/web interface
- Multi-provider support (Volcengine only for MVP)
- Image editing beyond regeneration
- Asset management/storage service

### 1.3 Definitions & Acronyms

| Term | Definition |
|------|------------|
| Golden Sample | A perfected reference image used as style template for batch generation |
| Series | A collection of related images (e.g., icon set) defined in YAML |
| Template | YAML file with variable placeholders for prompt generation |

---

## 2. Product Overview

### 2.1 Product Vision

Become the go-to CLI tool for developers who need consistent, production-ready AI-generated visual assets—eliminating the painful "last 10%" refinement cycle through template-driven batch workflows.

### 2.2 Goals & Objectives

| Goal | Target |
|------|--------|
| Time to first usable asset | < 5 minutes |
| Iteration cycle time | < 30 seconds |
| Batch generation (10 images) | < 3 minutes |
| Export to all sizes | < 10 seconds |
| Config learning curve | < 15 minutes |

**Additional Objectives:**
- Reduce manual prompt tweaking through templates
- Ensure style consistency across image series
- Provide cost visibility before API calls

### 2.3 Target Users

**Primary:** Mobile application developers who need themed visual assets

**Characteristics:**
- Comfortable with CLI tools
- Prefer YAML-based configuration
- Need multiple asset sizes (iOS @1x/@2x/@3x, Android density buckets)
- Need configurable custom dimensions (square, specific pixels)
- Value iteration speed over manual control

---

## 3. Features & Requirements

### 3.1 Core Features (MVP - Phase 1)

| Feature | Description | Priority |
|---------|-------------|----------|
| Project Init | `img init` creates session structure | P0 |
| YAML Config | 3-layer config system (global → project → per-image) | P0 |
| Volcengine Integration | API client for Jimeng AI image generation | P0 |
| Basic Generate | Single image generation from prompt | P0 |
| Template Engine | Variable substitution in prompts | P0 |
| Series Generation | Batch generate from series.yaml | P1 |
| History Tracking | Log iterations with prompts/params | P1 |
| Export Profiles | Configurable sizes (iOS/Android presets + custom dimensions) | P1 |

### 3.2 Secondary Features (Phase 2)

| Feature | Description | Priority |
|---------|-------------|----------|
| Refine Command | Iterative improvement on existing image | P1 |
| Golden Sample Lock | Mark sample as style reference | P1 |
| Batch Apply | Apply refinements across series | P1 |
| Dry Run Mode | Preview what will generate | P2 |
| Cost Estimator | Calculate API cost before run | P2 |

### 3.3 Future Considerations (Phase 3)

| Feature | Description | Priority |
|---------|-------------|----------|
| Prompt Linter | Warn about common prompt issues | P2 |
| Watch Mode | Auto-regenerate on config change | P2 |
| Diff/Rollback | Compare iterations, restore previous | P3 |
| Fix Presets | Common fixes as flags (e.g., `--fix transparency`) | P3 |

---

## 4. Technical Requirements

### 4.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| CLI Framework | Click |
| Config Parser | PyYAML |
| API Client | Volcengine SDK / httpx |
| Image Processing | Pillow |
| Version Tracking | JSON-based history |

### 4.2 Integrations

**Primary Integration:**
- **Provider:** Volcengine Jimeng AI (即梦AI)
- **Documentation:** https://www.volcengine.com/docs/85621/1537648?lang=zh
- **Auth:** API key via environment variable (`VOLCENGINE_API_KEY`)
- **Recommended Models:** 图片生成4.0 or 文生图3.1

**Available Capabilities:**
- Text-to-image (文生图)
- Image-to-image (图生图) — for style reference
- Inpainting (交互编辑) — for partial fixes

### 4.3 Constraints & Limitations

| Constraint | Details |
|------------|---------|
| API Provider | Volcengine Jimeng AI only (MVP) |
| Recommended Model | 图片生成4.0 or 文生图3.1 |
| Inpainting | Supported via separate endpoint |
| Style Reference | Possible via 图生图3.0 (image-to-image) |
| Rate Limits | TBD (requires API spike) |
| Pricing | TBD (see 产品计费 documentation) |
| Seed Preservation | TBD (requires API validation) |

### 4.4 Directory Structure

```
imgcreator/
├── cli/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── commands/
│   │   ├── init.py
│   │   ├── generate.py
│   │   ├── refine.py
│   │   ├── export.py
│   │   └── history.py
├── core/
│   ├── config.py         # Config loading/merging
│   ├── template.py       # Prompt template engine
│   ├── pipeline.py       # Generation pipeline
│   └── history.py        # Iteration tracking
├── api/
│   ├── volcengine.py     # API client
│   └── base.py           # Abstract provider interface
├── export/
│   ├── profiles.py       # iOS/Android profiles
│   └── resize.py         # Image resizing
└── utils/
    ├── lint.py           # Prompt linter
    └── cost.py           # Cost estimator
```

---

## 5. User Experience

### 5.1 Key User Flows

**Flow 1: Template Setup**
```
User defines series in YAML → specifies icon subjects, style preferences, constraints
```

**Flow 2: Sample Generation**
```
img generate --sample → CLI generates single sample based on YAML config
```

**Flow 3: LLM-Assisted Iteration (core workflow)**
```
User reviews sample → describes issues to Cursor/LLM agent 
→ Agent updates YAML template (prompt, params, style) 
→ Regenerate sample → repeat until perfect
```

**Flow 4: Batch Generation**
```
img generate --series → batch generate all icons using perfected YAML config
→ img export --all → production assets
```

**Key Insight:** The CLI is the execution engine; the LLM agent is the iteration interface for refining YAML configs.

### 5.2 Interface Requirements

**CLI Interface:**
- Clean, scriptable commands (`img init`, `img generate`, `img export`)
- Machine-readable output (`--output-format json|yaml|text`)
- `--verbose` / `-v` flag for detailed output (API calls, timing, config resolution)
- Clear error messages with actionable suggestions
- `--dry-run` for previewing without API calls

**YAML Configuration:**
- Human-readable and LLM-editable format
- Well-documented schema with examples
- Validation with helpful error messages
- Comments supported for context

**LLM Agent Integration:**
- Config files designed for easy LLM modification
- Predictable file structure for agent navigation
- Output includes paths to generated assets for agent reference

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target |
|--------|--------|
| Sample generation | < 30 seconds (API dependent) |
| Batch of 10 images | < 3 minutes |
| Export processing | < 10 seconds |

### 6.2 Security

- API keys via environment variables only (never in config files)
- No sensitive data logged in verbose mode

### 6.3 Reliability

- Graceful API failure handling with retry logic
- Resume interrupted batch operations
- Local history preserved on failures

---

## 7. Success Metrics

### 7.1 Key Performance Indicators

| KPI | Target |
|-----|--------|
| Time to first usable asset | < 5 minutes |
| Iteration cycle time | < 30 seconds |
| Batch generation (10 images) | < 3 minutes |
| Export to all sizes | < 10 seconds |
| Config learning curve | < 15 minutes |
| LLM iterations to perfect sample | ≤ 5 rounds |
| Series style consistency | Subjective, user-rated |

### 7.2 Acceptance Criteria

| # | Criterion |
|---|-----------|
| 1 | `img init` creates valid project structure with config files |
| 2 | `img generate` produces image from YAML-defined prompt |
| 3 | Template variables resolve correctly in prompts |
| 4 | `img generate --series` batch generates all items in series.yaml |
| 5 | `img export` produces correctly sized assets (custom + profiles) |
| 6 | History tracks each generation with prompt/params |
| 7 | Config layering works (global → project → per-image) |
| 8 | LLM agent can modify YAML and trigger regeneration successfully |

---

## 8. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API rate limits | High | Medium | Implement backoff, batch queuing |
| API cost overruns | Medium | Medium | Cost estimator, confirmation prompts, `--dry-run` |
| Style inconsistency across series | High | Medium | Golden sample + image-to-image reference |
| Template complexity | Medium | Low | Good defaults, examples, schema validation |
| Volcengine API changes | Medium | Low | Abstract provider interface for flexibility |
| Seed not supported | Medium | Medium | Rely on image-to-image for consistency |

---

## 9. Timeline & Milestones

### 9.1 Development Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| Phase 1 | MVP (init, config, generate, export) | 2-3 weeks |
| Phase 2 | Refinement workflow (refine, golden sample, batch apply) | 1-2 weeks |
| Phase 3 | DX features (lint, watch, diff/rollback) | 1-2 weeks |

### 9.2 Key Milestones

1. API spike complete (validate Volcengine capabilities)
2. Project structure setup
3. MVP: First end-to-end generation workflow
4. Export profiles working
5. Phase 2: Golden sample batch workflow
6. Phase 3: Developer experience polish

---

## 10. Appendix

### 10.1 References

- [Volcengine Jimeng AI Documentation](https://www.volcengine.com/docs/85621/1537648?lang=zh)
- PROJECT_BRIEF.md (source document)

### 10.2 Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Does Volcengine API support seed parameter? | TBD - API spike |
| 2 | Exact rate limits and pricing? | TBD - check 产品计费 docs |
| 3 | Best model for icon generation (3.1 vs 4.0)? | TBD - testing |
| 4 | Image-to-image workflow for style consistency? | TBD - validate approach |

---

*Document generated by PM Agent (John) using BMAD framework*

