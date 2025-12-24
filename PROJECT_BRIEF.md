# Project Brief: AI Image Series Creator CLI

## Executive Summary

A CLI tool that enables mobile app developers to rapidly create themed image series (icons, assets) using AI image generation, with a focus on solving the "last 10%" refinement problem through template-based workflows, golden sample iteration, and batch processing.

---

## Problem Statement

### The Challenge
Mobile app developers need cohesive themed visual assets (icons, graphics). Current AI image generators produce images that are **90% right**, but the **last 10% refinement** is disproportionately time-consuming—requiring repeated prompt tweaking, regeneration, and manual selection.

### Specific Pain Points
| Issue | Description |
|-------|-------------|
| Iteration Friction | Re-prompting is slow and loses context |
| Consistency | Hard to maintain style across a series |
| Detail Problems | Background transparency, anatomy errors (e.g., extra limbs), small artifacts |
| No Batch Fix | Improvements to one image must be manually replicated |
| Export Overhead | Manual resizing for iOS/Android asset requirements |

### Desired Outcome
A streamlined workflow: **Generate → Perfect one sample → Apply to batch → Export production-ready assets**

---

## Target Users

**Primary:** Mobile application developers who need themed visual assets

**Characteristics:**
- Comfortable with CLI tools
- Prefer YAML-based configuration
- Need multiple asset sizes (iOS @1x/@2x/@3x, Android density buckets)
- Value iteration speed over manual control

---

## Solution Overview

### Tool Name
`imgcreator` (working title)

### Core Concept
**Session + Pipeline + Templates**

```
PROJECT SESSION
├── config.yaml          # Project configuration
├── templates/           # Reusable prompt templates
├── series.yaml          # Image series definition
├── .history/            # Iteration tracking
├── outputs/             # Generated images
└── exports/             # Final sized assets
```

### Key Differentiators
1. **Golden Sample Workflow** - Perfect one image, batch-apply to series
2. **Template Engine** - Variables in prompts for consistent series
3. **Developer-First DX** - Dry-run, lint, cost estimates, watch mode
4. **3-Layer Config** - Global defaults → Project → Per-image overrides

---

## Core Features

### MVP (Phase 1)

| Feature | Description | Priority |
|---------|-------------|----------|
| Project Init | `img init` creates session structure | P0 |
| YAML Config | Layered configuration system | P0 |
| Volcengine Integration | API client for image generation | P0 |
| Basic Generate | Single image generation from prompt | P0 |
| Template Engine | Variable substitution in prompts | P0 |
| Series Generation | Batch generate from series.yaml | P1 |
| History Tracking | Log iterations with prompts/params | P1 |
| Export Profiles | iOS/Android preset sizes | P1 |

### Phase 2

| Feature | Description | Priority |
|---------|-------------|----------|
| Refine Command | Iterative improvement on existing image | P1 |
| Golden Sample Lock | Mark sample as style reference | P1 |
| Batch Apply | Apply refinements across series | P1 |
| Dry Run Mode | Preview what will generate | P2 |
| Cost Estimator | Calculate API cost before run | P2 |

### Phase 3

| Feature | Description | Priority |
|---------|-------------|----------|
| Prompt Linter | Warn about common issues | P2 |
| Watch Mode | Auto-regenerate on config change | P2 |
| Diff/Rollback | Compare iterations, restore previous | P3 |
| Fix Presets | Common fixes as flags | P3 |

---

## Technical Architecture

### Tech Stack
| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| CLI Framework | Click or Typer |
| Config Parser | PyYAML |
| API Client | Volcengine SDK / httpx |
| Image Processing | Pillow |
| Version Tracking | JSON-based history |

### API Integration
- **Provider:** Volcengine (ByteDance)
- **Endpoint:** https://www.volcengine.com/docs/85621/1537648
- **Auth:** API key (environment variable)
- **Default Model:** Nano Banana (configurable)

### Directory Structure
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

## CLI Interface

### Commands
```bash
# Project Management
img init <name>              # Create new project
img status                   # Show project state

# Generation
img generate [options]       # Generate images
  --template <name>          # Use prompt template
  --series                   # Generate full series
  --dry-run                  # Preview without API call
  --execute                  # Skip confirmation

# Refinement
img refine <id> [options]    # Improve existing image
  --fix "<instruction>"      # What to fix
  --lock                     # Mark as golden sample

# Batch Operations
img batch --from-sample <id> # Apply sample to series

# Export
img export [options]         # Export sized assets
  --profile <ios|android>    # Export profile
  --all                      # All profiles

# Utilities
img lint                     # Check prompts
img estimate                 # Show cost estimate
img watch                    # Auto-regenerate mode
img history                  # Show iterations
img rollback <version>       # Restore previous
```

---

## Configuration Schema

### Global Config (`~/.imgcreator/config.yaml`)
```yaml
api:
  provider: volcengine
  key_env: VOLCENGINE_API_KEY
  
defaults:
  model: nano-banana
  width: 1024
  height: 1024
  negative_prompt: "blurry, deformed, extra limbs, bad anatomy"
```

### Project Config (`./config.yaml`)
```yaml
project:
  name: my-app-icons
  description: Icon set for MyApp
  
style:
  base: "flat design, minimal, modern app icon"
  background: transparent
  
export_profiles:
  ios:
    sizes: [60, 120, 180]
    format: png
  android:
    sizes: [48, 72, 96, 144, 192]
    format: png
```

### Series Definition (`./series.yaml`)
```yaml
template: app-icon

series:
  - id: home
    subject: house
    
  - id: settings
    subject: gear
    
  - id: profile
    subject: person silhouette
    overrides:
      background: "soft gradient"
```

### Prompt Template (`./templates/app-icon.yaml`)
```yaml
name: app-icon
base_prompt: "a {subject} icon, {style}, {background}"

variables:
  subject: 
    required: true
  style: 
    default: "flat design, minimal, modern"
  background:
    default: "transparent background, no background"

negative_prompt:
  - "realistic"
  - "3d render"
  - "photograph"
  - "extra limbs"
  - "deformed"
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to first usable asset | < 5 minutes |
| Iteration cycle time | < 30 seconds |
| Batch generation (10 images) | < 3 minutes |
| Export to all sizes | < 10 seconds |
| Config learning curve | < 15 minutes |

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API rate limits | High | Medium | Implement backoff, batch queuing |
| API cost overruns | Medium | Medium | Cost estimator, confirmation prompts |
| Style inconsistency | High | Medium | Golden sample + seed preservation |
| Template complexity | Medium | Low | Good defaults, examples |

---

## Timeline (Estimated)

| Phase | Scope | Duration |
|-------|-------|----------|
| Phase 1 | MVP (init, config, generate, export) | 2-3 weeks |
| Phase 2 | Refinement workflow | 1-2 weeks |
| Phase 3 | DX features (lint, watch, etc.) | 1-2 weeks |

---

## Open Questions

1. **Seed Preservation** - Does Volcengine API support seed for reproducibility?
2. **Inpainting** - Does the API support partial regeneration for fixes?
3. **Style Reference** - Can we pass a reference image for style consistency?
4. **Rate Limits** - What are the API rate limits and pricing?

---

## Next Steps

1. [ ] Validate Volcengine API capabilities (spike)
2. [ ] Set up project structure in `Malden_image_creator`
3. [ ] Implement MVP: init, config, basic generate
4. [ ] Test with real icon generation workflow
5. [ ] Iterate based on usage

---

*Document created: December 2024*
*Status: Draft*

