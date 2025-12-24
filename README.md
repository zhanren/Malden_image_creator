# Malden Image Creator

AI-powered CLI tool for generating themed image series using Volcengine Jimeng AI. Create consistent icon sets and visual assets with template-based workflows and batch processing.

## Features

- 🚀 **Quick Setup** - Initialize projects in seconds
- 🎨 **Template Engine** - Reusable prompts with variable substitution
- 📦 **Series Generation** - Batch generate consistent icon sets
- 📱 **Export Profiles** - iOS (@1x/@2x/@3x) and Android (density buckets) support
- 📊 **History Tracking** - Review past generations and iterate
- ⚙️ **3-Layer Config** - Global → Project → Per-image configuration

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd Malden_image_creator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Environment Variables

### Required

You need to set Volcengine API credentials. Choose one of these methods:

#### Method 1: .env File (Recommended)

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env and add your credentials
# VOLCENGINE_ACCESS_KEY_ID=your_access_key_id
# VOLCENGINE_SECRET_ACCESS_KEY=your_secret_access_key
```

The CLI automatically loads `.env` files from the project directory.

#### Method 2: Environment Variables

```bash
# Set in your shell session
export VOLCENGINE_ACCESS_KEY_ID=your_access_key_id
export VOLCENGINE_SECRET_ACCESS_KEY=your_secret_access_key
```

**Note:** Environment variables set in your shell take precedence over `.env` file values.

## Quick Start

### 1. Initialize a Project

```bash
img init
```

This creates:
- `imgcreator.yaml` - Project configuration
- `series/` - Directory for series definitions
- `output/` - Directory for generated images
- `history/` - Directory for generation history
- `.env.example` - Template for API keys

### 2. Configure API Keys

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
# VOLCENGINE_ACCESS_KEY_ID=your_key_id
# VOLCENGINE_SECRET_ACCESS_KEY=your_secret
```

### 3. Generate Your First Image

```bash
# Generate a single image
img generate --prompt "flat minimal icon of a home"

# Or use dry-run to preview
img generate --prompt "cat icon" --dry-run
```

## CLI Commands

### `img init [NAME]`

Initialize a new imgcreator project.

```bash
img init                    # Initialize in current directory
img init my-project         # Create named project folder
img init --force            # Reinitialize existing project
```

### `img generate`

Generate images from prompts or series.

**Single Image Generation:**
```bash
img generate --prompt "flat icon of a cat"
img generate --prompt "icon" --width 512 --height 512
img generate --prompt "icon" --style "pixel art" --seed 42
img generate --sample                    # Generate sample image
img generate --dry-run                   # Preview without API call
```

**Series Generation:**
```bash
img generate --series app-icons          # Generate from named series
img generate --series                    # Use default series (if only one)
img generate --series app-icons --limit 2 # Generate first 2 items
img generate --series app-icons --dry-run # Preview all prompts
```

**Options:**
- `-p, --prompt TEXT` - Generation prompt
- `-w, --width INTEGER` - Image width in pixels
- `-h, --height INTEGER` - Image height in pixels
- `-m, --model TEXT` - Model to use (图片生成4.0, 文生图3.1)
- `-s, --style TEXT` - Style prefix for prompt
- `--seed INTEGER` - Random seed for reproducibility
- `-o, --output PATH` - Output directory
- `--series TEXT` - Generate from series
- `--limit INTEGER` - Limit number of items (for series)
- `--sample` - Generate single sample image
- `--dry-run` - Preview without making API call
- `--output-format [text|json|yaml]` - Output format

### `img export`

Export images to multiple sizes (iOS, Android, custom).

```bash
img export image.png --profile ios        # iOS @1x/@2x/@3x
img export image.png --profile android    # Android densities
img export image.png --size 100x100      # Custom size
img export *.png --all                    # All profiles
img export --dry-run                      # Preview exports
```

**Options:**
- `--profile [ios|android]` - Export profile
- `--size TEXT` - Custom size (e.g., 100x100)
- `--all` - Apply all configured profiles
- `-o, --output PATH` - Output directory (default: export/)
- `--maintain-aspect / --no-maintain-aspect` - Aspect ratio handling
- `--dry-run` - Preview without exporting
- `--output-format [text|json|yaml]` - Output format

**Output Structure:**
```
export/
├── ios/
│   ├── image@1x.png
│   ├── image@2x.png
│   └── image@3x.png
├── android/
│   ├── mdpi/image.png
│   ├── hdpi/image.png
│   └── ...
└── custom/
    └── image_100x100.png
```

### `img history`

View generation history.

```bash
img history                    # List recent generations
img history <id>               # Show details of specific entry
img history --limit 10         # Show last 10 entries
img history --series app-icons # Filter by series
img history --search "icon"    # Search in prompts
img history --status failed    # Filter by status
img history --stats            # Show statistics
```

**Options:**
- `-n, --limit INTEGER` - Limit number of entries
- `--series TEXT` - Filter by series name
- `--status [success|failed]` - Filter by status
- `-s, --search TEXT` - Search in prompts
- `--stats` - Show history statistics
- `--output-format [text|json|yaml]` - Output format

### `img config`

Display or validate project configuration.

```bash
img config                     # Show resolved config
img config --validate          # Validate config only
img config --global            # Show global config path
img config --test-auth         # Test API authentication
img --verbose config           # Verbose loading info (note: --verbose is global)
```

**Options:**
- `-c, --validate` - Validate configuration only
- `--global` - Show global config location
- `--test-auth` - Test API authentication
- `--output-format [text|json|yaml]` - Output format

**Note:** `--verbose` is a global option. Use `img --verbose config` (not `img config --verbose`).

### Global Options

All commands support these options when placed **before** the command:

- `-v, --verbose` - Enable verbose output
- `--help` - Show command help
- `--version` - Show version

**Usage:**
```bash
img --verbose generate --prompt "test"  # ✓ Correct
img generate --verbose --prompt "test"  # ✗ Wrong (--verbose must come first)
```

## Series Definition

Create series files in the `series/` directory:

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
```

Then generate:
```bash
img generate --series app-icons
```

## Configuration

### Project Config (`imgcreator.yaml`)

```yaml
api:
  provider: volcengine
  model: "图片生成4.0"

defaults:
  width: 1024
  height: 1024
  style: "flat, minimal, modern"

output:
  base_dir: ./output
```

### Global Config (`~/.imgcreator/config.yaml`)

Optional global configuration that applies to all projects:

```yaml
api:
  timeout: 120

defaults:
  style: "global default style"
```

**Config Precedence:** Per-image > Project > Global

## Testing

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=imgcreator --cov-report=html

# Run specific test file
pytest tests/test_config.py -v

# Run specific test
pytest tests/test_config.py::TestConfigLoader::test_load_project_config -v
```

### Test Commands

```bash
# Test init command
img init test-project
cd test-project
img config

# Test generate (dry-run, no API call)
img generate --prompt "test icon" --dry-run

# Test export (requires test image)
# Create a test image first, then:
img export test.png --profile ios --dry-run

# Test history (after generating)
img history
img history --stats
```

### Linting

```bash
# Check code style
ruff check imgcreator/ tests/

# Auto-fix issues
ruff check --fix imgcreator/ tests/
```

## Examples

### Example 1: Generate Icon Set

```bash
# 1. Initialize project
img init icon-project
cd icon-project

# 2. Create series definition
cat > series/icons.yaml << EOF
name: icons
template: "{{style}} icon of {{subject}}"
defaults:
  style: "flat minimal"
config:
  width: 512
  height: 512
items:
  - id: home
    subject: "home house"
  - id: settings
    subject: "gear"
EOF

# 3. Generate series
img generate --series icons

# 4. Export to iOS sizes
img export output/*.png --profile ios
```

### Example 2: Iterative Refinement

```bash
# Generate sample
img generate --prompt "cat icon" --sample

# Review and refine
img generate --prompt "flat minimal cat icon, centered" --style "pixel art"

# Check history
img history
img history <entry_id>  # View details

# Export final version
img export output/cat_*.png --profile ios --profile android
```

## Project Structure

```
project/
├── imgcreator.yaml      # Project configuration
├── .env                 # API keys (not in git)
├── series/              # Series definitions
│   └── app-icons.yaml
├── output/              # Generated images
├── history/             # Generation history
└── export/             # Exported assets
    ├── ios/
    ├── android/
    └── custom/
```

## Troubleshooting

### API Authentication Errors

#### Error: "Authentication failed"

If you see:
```
✗ [volcengine] Authentication failed. Check your Access Key ID and Secret.
```

**Solutions:**

1. **Test your credentials:**
   ```bash
   img config --test-auth
   ```

2. **Verify environment variables are set:**
   ```bash
   # Check if variables are loaded
   echo $VOLCENGINE_ACCESS_KEY_ID
   echo $VOLCENGINE_SECRET_ACCESS_KEY
   ```

3. **Use .env file (recommended):**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env and add your credentials
   nano .env  # or use your preferred editor
   ```

4. **Check credentials format:**
   - Ensure no extra spaces or quotes
   - Access Key ID should be a string (e.g., `AKIA...`)
   - Secret Access Key should be a string (e.g., `wJalr...`)

5. **Use verbose mode for details:**
   ```bash
   img --verbose generate --prompt "test"
   ```

6. **Verify API permissions (especially for 50400 "Access Denied"):**
   - **If you see "Access Denied" (50400):** Your credentials are likely correct, but:
     - The 即梦AI (Jimeng AI) sub-service may need separate activation
     - Even if "智能视觉" (Intelligent Vision) shows recent access, Jimeng AI may need specific permissions
     - Check IAM policies for Visual AI service permissions
     - Activate 即梦AI service specifically in your Volcengine console
     - Verify service activation: https://console.volcengine.com/
   - Ensure your API key has permissions for the Visual AI service
   - Check that you're using the correct region (cn-north-1 / 华北1)

### Config Not Found

```
✗ Project config not found: imgcreator.yaml
```

**Solution:** Run `img init` to create project structure.

### No Images to Export

```
✗ No images found to export
```

**Solution:** Generate images first or specify image paths:
```bash
img export path/to/image.png --profile ios
```

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=imgcreator

# Specific module
pytest tests/test_export.py -v
```

### Code Quality

```bash
# Linting
ruff check imgcreator/ tests/

# Type checking (if using mypy)
mypy imgcreator/
```

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.
