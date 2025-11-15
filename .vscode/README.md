# Cursor/VS Code Configuration Guide

This directory contains configuration files for Cursor (and VS Code) to match the project's formatting and linting requirements.

## Required Extensions

Install the following extensions in Cursor:

### Essential Extensions

1. **Ruff** (`charliermarsh.ruff`)
   - Python linter and formatter
   - Replaces Black, isort, flake8, etc.
   - Auto-fixes on save

2. **Python** (`ms-python.python`)
   - Python language support
   - IntelliSense, debugging, etc.

3. **Pylance** (`ms-python.vscode-pylance`)
   - Fast Python language server
   - Type checking and code completion
   - **Note:** VS Code 1.99.3 compatible with Pylance 2025.6.2 (see `.vscode/COMPATIBILITY.md`)

4. **YAML** (`redhat.vscode-yaml`)
   - YAML language support
   - Formatting and validation

### Recommended Extensions

5. **GitLens** (`eamodio.gitlens`)
   - Enhanced Git capabilities

6. **Markdown All in One** (`yzhang.markdown-all-in-one`)
   - Markdown editing support (table of contents, shortcuts, etc.)
   - **Note:** Not used for formatting, only for editing assistance

7. **Markdownlint** (`davidanson.vscode-markdownlint`)
   - Markdown linting and formatting
   - **Default formatter** for Markdown files
   - Auto-fixes linting issues on save

8. **EditorConfig** (`editorconfig.editorconfig`)
   - Consistent coding styles

## Installation

### Method 1: Automatic (Recommended)

1. Open the project in Cursor
2. When prompted, click "Install" to install recommended extensions
3. Or manually: `Cmd+Shift+P` → "Extensions: Show Recommended Extensions"

### Method 2: Manual

1. Open Extensions view: `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)
2. Search and install each extension listed above

## Configuration Files

### `.vscode/settings.json`
- Configures Ruff as the default Python formatter
- Configures Markdownlint as the default Markdown formatter
- Sets up YAML formatting
- Enables format on save for all supported file types
- Configures editor rulers (88 for Python, 120 for YAML and Markdown)

### `.vscode/extensions.json`
- Lists recommended extensions
- Lists unwanted extensions (conflicting formatters)

### `.vscode/tasks.json`
- Defines tasks for:
  - Format code
  - Check formatting
  - Lint code
  - Fix lint issues
  - Check YAML
  - Run tests
  - Pre-commit checks

### `.vscode/launch.json`
- Debug configurations for:
  - Current Python file
  - Main script
  - Pytest tests

## Usage

### Format on Save
- Enabled by default
- Automatically formats Python files using Ruff on save
- Automatically formats Markdown files using Markdownlint on save
- Automatically fixes Markdown linting issues on save

### Manual Formatting
- `Shift+Alt+F` (Windows/Linux) or `Shift+Option+F` (Mac)
- Or: `Cmd+Shift+P` → "Format Document"

### Run Tasks
- `Cmd+Shift+P` → "Tasks: Run Task"
- Select a task (e.g., "Lint Code (ruff)")

### Keyboard Shortcuts
- Format Document: `Shift+Alt+F` / `Shift+Option+F`
- Run Task: `Cmd+Shift+P` → "Tasks: Run Task"

## Verification

After installation, verify the setup:

1. **Python Formatting**
   - Open a Python file
   - Make a formatting change (e.g., add extra spaces)
   - Save the file (`Cmd+S` / `Ctrl+S`)
   - The file should auto-format using Ruff

2. **Markdown Formatting**
   - Open a Markdown file
   - Make a formatting change (e.g., add trailing spaces, fix list formatting)
   - Save the file (`Cmd+S` / `Ctrl+S`)
   - The file should auto-format using Markdownlint
   - Linting issues should be automatically fixed

## Troubleshooting

### Ruff not working
1. Ensure Ruff extension is installed
2. Check Python interpreter: `Cmd+Shift+P` → "Python: Select Interpreter"
3. Verify `uv` is available: `uv --version`
4. Reload window: `Cmd+Shift+P` → "Developer: Reload Window"

### YAML not formatting
1. Ensure YAML extension is installed
2. Check file association (should be `.yaml` or `.yml`)
3. Reload window

### Format on save not working
1. Check settings: `Cmd+,` → search "format on save"
2. Ensure "Editor: Format On Save" is enabled
3. Check file type is recognized (Python files should show "Python" in status bar)

## Project-Specific Settings

The project uses:
- **Ruff** for Python formatting and linting (replaces Black)
- **Yamllint** for YAML validation
- **uv** as the package manager
- Line length: 88 for Python, 120 for YAML
- Python 3.10+ required

## CI/CD Alignment

These settings match the CI workflow (`.github/workflows/ci.yml`):
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run yamllint . --config-file .yamllint || true`
