# Development Guide

This document provides detailed information for developers working on the Cloud Certificate Renewer project.

## Table of Contents

- [Environment Setup](#environment-setup)
  - [Requirements](#requirements)
  - [Quick Start](#quick-start)
  - [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [Code Formatting](#code-formatting)
- [Code Linting](#code-linting)
- [YAML File Formatting](#yaml-file-formatting)
- [Test Execution](#test-execution)
- [Building Docker Image](#building-docker-image)
- [Code Structure](#code-structure)

## Environment Setup

### Requirements

- Python 3.10+
- uv (Python package manager)

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd cloud-cert-renewer

# 2. Install dependencies
uv sync --extra dev

# 3. Configure environment variables
cp .env.example .env
# Edit .env file and fill in your configuration

# 4. Run the program
uv run python main.py

# Run with arguments
uv run python main.py --help
uv run python main.py --dry-run
```

### Detailed Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies and development dependencies
uv sync --extra dev
```

## CLI Arguments

The application supports the following command-line arguments:

| Argument    | Short | Description                                                                              |
| ----------- | ----- | ---------------------------------------------------------------------------------------- |
| `--help`    | `-h`  | Show help message and exit                                                               |
| `--version` |       | Show program's version number and exit                                                   |
| `--verbose` | `-v`  | Enable verbose logging (DEBUG level)                                                     |
| `--quiet`   | `-q`  | Enable quiet logging (WARNING level)                                                     |
| `--dry-run` |       | Perform a trial run without making any changes (validates certificate and configuration) |

**Examples:**

```bash
# Check version
uv run python main.py --version

# Run in dry-run mode with verbose logging
uv run python main.py --dry-run --verbose

# Run in quiet mode
uv run python main.py --quiet
```

## Configuration

The project supports configuration via environment variables or `.env` files. Refer to `.env.example` to create your `.env` file.

### Required Environment Variables

**Note:** When using OIDC authentication (`AUTH_METHOD=oidc`), `CLOUD_ACCESS_KEY_ID` and `CLOUD_ACCESS_KEY_SECRET` are NOT required.

- `CLOUD_ACCESS_KEY_ID`: Cloud service AccessKey ID (new name, preferred, not required for OIDC)
- `CLOUD_ACCESS_KEY_SECRET`: Cloud service AccessKey Secret (new name, preferred, not required for OIDC)
- `SERVICE_TYPE`: Service type, options: `cdn` or `lb` (backward compatible: `slb`)

### Optional Environment Variables

- `CLOUD_PROVIDER`: Cloud provider, options: `alibaba`, `aws`, `azure`, etc. (default: `alibaba`)
- `AUTH_METHOD`: Authentication method, options: `access_key`, `sts`, `iam_role`, `oidc`, `service_account`, `env` (default: `access_key`)
- `CLOUD_SECURITY_TOKEN`: STS temporary security token (optional, required when `AUTH_METHOD=sts`)

### SDK Configuration (Optional)

- `CLOUD_API_CONNECT_TIMEOUT`: API connection timeout in milliseconds (default: SDK default)
- `CLOUD_API_READ_TIMEOUT`: API read timeout in milliseconds (default: SDK default)
- `CLOUD_API_MAX_ATTEMPTS`: Maximum retry attempts for API calls (default: SDK default, enables auto-retry when set)

### OIDC Authentication (RRSA)

When using OIDC authentication (`AUTH_METHOD=oidc`), the following environment variables are automatically injected by Kubernetes Service Account and RRSA:

- `ALIBABA_CLOUD_ROLE_ARN` or `CLOUD_ROLE_ARN`: RAM Role ARN (automatically set from Service Account annotation)
- `ALIBABA_CLOUD_OIDC_PROVIDER_ARN` or `CLOUD_OIDC_PROVIDER_ARN`: OIDC Provider ARN (automatically set by RRSA)
- `ALIBABA_CLOUD_OIDC_TOKEN_FILE` or `CLOUD_OIDC_TOKEN_FILE`: Path to OIDC token file (automatically set by RRSA)

**Note:** When using OIDC authentication, `CLOUD_ACCESS_KEY_ID` and `CLOUD_ACCESS_KEY_SECRET` are NOT required. Credentials are fetched dynamically from OIDC.

**Reference:**

- [Alibaba Cloud RRSA Documentation](https://help.aliyun.com/zh/ack/serverless-kubernetes/user-guide/use-rrsa-to-authorize-pods-to-access-different-cloud-services)
- [Alibaba Cloud SDK Credentials Documentation](https://www.alibabacloud.com/help/en/sdk/developer-reference/v2-manage-python-access-credentials)
- `FORCE_UPDATE`: Force update certificate even if it's the same (default: `false`)

### CDN Configuration (when SERVICE_TYPE=cdn)

- `CDN_DOMAIN_NAME`: Comma-separated list of CDN domain names (e.g., `cdn1.example.com,cdn2.example.com`)
- `CDN_CERT`: SSL certificate content (PEM format, supports multi-line)
- `CDN_CERT_PRIVATE_KEY`: SSL certificate private key (PEM format, supports multi-line)
- `CDN_REGION`: Region (default: `cn-hangzhou`)

**Note for Helm Chart Users:**

In Helm Chart values files, `cdn.domainName` can be specified in two formats:

- **YAML list format (recommended)**: More readable and less error-prone, especially for long domain lists

  ```yaml
  cdn:
    domainName:
      - example.com
      - www.example.com
      - api.example.com
  ```

- **Comma-separated string (backward compatible)**: Still supported for compatibility

  ```yaml
  cdn:
    domainName: "example.com,www.example.com"
  ```

Both formats are automatically converted to the `CDN_DOMAIN_NAME` environment variable (comma-separated string) for the application.

### Load Balancer Configuration (when SERVICE_TYPE=lb or slb)

- `LB_INSTANCE_ID`: Comma-separated list of Load Balancer instance IDs (e.g., `lb-xxxxxxxx,lb-yyyyyyyy`) (new name, preferred)
- `LB_LISTENER_PORT`: Listener port (new name, preferred)
- `LB_CERT`: SSL certificate content (PEM format, supports multi-line) (new name, preferred)
- `LB_CERT_PRIVATE_KEY`: SSL certificate private key (PEM format, supports multi-line) (new name, preferred)
- `LB_REGION`: Region (default: `cn-hangzhou`) (new name, preferred)

### Legacy Environment Variables

For backward compatibility, the following legacy variable names are also supported:

- `ALIBABA_CLOUD_ACCESS_KEY_ID` → use `CLOUD_ACCESS_KEY_ID` instead
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET` → use `CLOUD_ACCESS_KEY_SECRET` instead
- `SLB_*` variables → use `LB_*` variables instead

### Certificate Format

In `.env` files, certificates and private keys can use multi-line format with triple quotes:

```env
CDN_CERT="""-----BEGIN CERTIFICATE-----
Certificate content...
-----END CERTIFICATE-----"""
```

This ensures the certificate content is not escaped or corrupted.

### Alibaba Cloud RAM Permissions

When using Alibaba Cloud, ensure your AccessKey has the appropriate RAM permissions. For detailed permission requirements and recommended policies, see the [Helm Chart README](../helm/cloud-cert-renewer/README.md#ram-permissions-alibaba-cloud).

**Quick Reference:**

- **CDN**: `cdn:SetCdnDomainSSLCertificate`, `cdn:DescribeDomainCertificateInfo`
- **Load Balancer**: `slb:DescribeServerCertificates`, `slb:UploadServerCertificate`, `slb:SetLoadBalancerHTTPSListenerAttribute`, `slb:DescribeLoadBalancerHTTPSListenerAttribute`

## Code Formatting

```bash
# Format code with ruff
uv run ruff format .

# Check code format (without modification)
uv run ruff format --check .
```

## Code Linting

```bash
# Lint check with ruff
uv run ruff check .

# Auto-fix issues with ruff
uv run ruff check . --fix
```

## YAML File Formatting

The project is configured with `yamllint` and `pre-commit` for YAML file checking and formatting.

### Using yamllint to check YAML files

```bash
# Check all YAML files
uv run yamllint . --config-file .yamllint

# Check specific file
uv run yamllint k8s/deployment.yaml --config-file .yamllint

# Check GitHub workflows (excludes Helm charts)
uv run yamllint .github/workflows/ --config-file .yamllint
```

**Note:** The `.yamllint` configuration sets `line-length` to `warning` level. While warnings won't fail pre-commit hooks, they should still be fixed before committing to maintain code quality. Run `yamllint` manually to check for warnings.

### Using pre-commit (recommended)

**Pre-commit hooks execution context:**

- **Local development**: Hooks run automatically before `git commit` and can **modify files** (auto-fix formatting, linting issues)
- **CI/CD (GitHub Workflows)**: Hooks run in **check-only mode** and **never modify files** to ensure CI consistency

```bash
# Install pre-commit hooks (automatically run on git commit)
uv run pre-commit install

# Manually run all checks (local: can modify files)
uv run pre-commit run --all-files

# Only check YAML files
uv run pre-commit run yamllint --all-files
```

**Note for CI/CD:**

In GitHub Workflows, the `pre-commit` job uses `SKIP` environment variable to skip hooks that modify files (`trailing-whitespace`, `end-of-file-fixer`, `ruff`, `ruff-format`, `prettier`). These checks are already performed by the `lint-and-format` job using read-only commands (`ruff format --check`, `ruff check`). This ensures:

- CI never modifies source code
- Build results are predictable and consistent
- Code quality is verified without side effects

### Recommended YAML formatting tools

1. **yamllint** (installed) - YAML syntax and style checking
   - Pros: Lightweight, fast, configurable
   - Cons: Does not directly format, only checks and reports issues

2. **pre-commit** (installed) - Git hook management tool
   - Pros: Integrates multiple tools, automated checking
   - Cons: Requires Git repository

3. **yamlfmt** (optional) - Dedicated YAML formatting tool

   ```bash
   # Install with Go
   go install github.com/google/yamlfmt/cmd/yamlfmt@latest
   ```

4. **prettier** (optional) - General code formatting tool

   ```bash
   # Install with npm
   npm install -g prettier
   prettier --write "**/*.yaml" "**/*.yml"
   ```

## Test Execution

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with print output
uv run pytest -s

# Run specific test file
uv run pytest tests/test_clients.py

# Run specific test class
uv run pytest tests/test_clients.py::TestCdnCertRenewer

# Run specific test method
uv run pytest tests/test_clients.py::TestCdnCertRenewer::test_create_client

# Stop at first failure
uv run pytest -x

# Show top 10 slowest tests
uv run pytest --durations=10

# Generate coverage report
uv run pytest --cov=. --cov-report=html
```

For more information about testing, see [testing-design-principles.mdc](testing-design-principles.mdc) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Building Docker Image

### Local Build (Single Architecture)

```bash
# Build image for current platform
docker build -t cloud-cert-renewer:latest .

# Build with specific tag
docker build -t cloud-cert-renewer:v0.1.0 .

# Test run image
docker run --rm \
  -e CLOUD_ACCESS_KEY_ID=your_key \
  -e CLOUD_ACCESS_KEY_SECRET=your_secret \
  -e SERVICE_TYPE=cdn \
  -e CLOUD_PROVIDER=alibaba \
  -e AUTH_METHOD=access_key \
  -e CDN_DOMAIN_NAME=example.com \
  -e CDN_CERT="$(cat cert.pem)" \
  -e CDN_CERT_PRIVATE_KEY="$(cat key.pem)" \
  cloud-cert-renewer:latest
```

### Multi-Architecture Build

The project supports building Docker images for multiple architectures (amd64 and arm64). For local multi-architecture builds, use Docker Buildx:

```bash
# Create and use a buildx builder instance
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t cloud-cert-renewer:latest \
  --push .

# Or build without pushing (load to local)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t cloud-cert-renewer:latest \
  --load .
```

**Note:** The GitHub Actions release workflow automatically builds and publishes multi-architecture images (amd64 and arm64) to both GitHub Container Registry (GHCR) and Docker Hub (if configured). Both registries contain identical image content with the same digest for each architecture. No manual multi-architecture build is required for releases.

## Release Workflow

The project includes a comprehensive release workflow that publishes all artifacts (Docker images, Helm Charts, and PyPI packages) with unified version management.

### Prerequisites

1. **PyPI Account**: Register at [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/)
2. **API Token**: Create an API token in your PyPI account settings:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/) → API tokens
   - Create a new API token with scope: **Entire account** (for publishing)
   - Copy the token (it starts with `pypi-`)
3. **GitHub Secrets**: Add the following secrets to your GitHub repository:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add secret `PYPI_API_TOKEN` with your PyPI API token
   - Add secret `TEST_PYPI_API_TOKEN` with your TestPyPI API token (optional, for testing)
   - **Docker Hub** (optional, for publishing to Docker Hub):
     - Add secret `DOCKERHUB_USERNAME` with your Docker Hub username
     - Add secret `DOCKERHUB_TOKEN` with your Docker Hub access token
     - To create a Docker Hub access token:
       1. Go to [Docker Hub Account Settings](https://hub.docker.com/settings/security)
       2. Click **New Access Token**
       3. Give it a name (e.g., "GitHub Actions")
       4. Set permissions to **Read, Write & Delete** (all three permissions are required for updating repository descriptions)
       5. Copy the token (you'll only see it once)
     - **Note**: The token must have `read`, `write`, and `delete` permissions for the `dockerhub-description` action to work. If you get a "Forbidden" error, verify your token has all three permissions.
4. **GitHub Pages**: Enable GitHub Pages for Helm Chart repository:
   - Go to **Settings** → **Pages**
   - Source: **Deploy from a branch**
   - Branch: `gh-pages` / `/(root)`

### Publishing via GitHub Actions (Recommended)

The project includes a unified release workflow (`.github/workflows/release.yml`) that publishes all artifacts with automated version synchronization, testing, and quality checks.

#### Manual Release

1. Go to **Actions** tab in your GitHub repository
2. Select **Release** workflow
3. Click **Run workflow**
4. Configure the workflow inputs:
   - **Version**: Optional. Leave empty to use version from `pyproject.toml` or extract from Git tag
   - **Release type**: Choose `release`, `pre-release`, or `test`
     - `release`: Full release with all artifacts, creates Git tag and GitHub Release
     - `pre-release`: Release candidate (e.g., `0.1.0-rc.1`), publishes to all repositories
     - `test`: Test build (e.g., `0.1.0-test`), publishes to TestPyPI and test Docker tags
   - **Publish Docker**: Check to publish Docker image to ghcr.io (default: true)
   - **Publish Helm**: Check to publish Helm Chart to GitHub Pages (default: true)
   - **Publish PyPI**: Check to publish PyPI package (default: true)
5. Click **Run workflow**

The workflow will:

- Synchronize versions across all files (`pyproject.toml`, `__init__.py`, `Chart.yaml`)
- Run tests and code quality checks
- Build distribution packages
- Build and publish multi-architecture Docker images (amd64 and arm64)
- Package and publish Helm Chart to GitHub Pages
- Publish PyPI package to PyPI or TestPyPI (based on release type)
- Create Git tag (for release type)
- Create GitHub Release with all artifacts (for release type)

### Automatic Release on Tag Push

You can also trigger a release by pushing a Git tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

When a tag matching `v*` is pushed, the workflow will automatically:

- Extract version from tag (e.g., `v0.1.0` → `0.1.0`)
- Synchronize versions across all files (`pyproject.toml`, `__init__.py`, `Chart.yaml`)
- Run tests and code quality checks
- Build distribution packages
- Build and publish multi-architecture Docker images (amd64 and arm64) to ghcr.io
- Package and publish Helm Chart to GitHub Pages (gh-pages branch)
- Publish PyPI package to PyPI
- Create GitHub Release with release notes from `CHANGELOG.md` and all artifacts

**Note:** Tag-based releases always publish all artifacts (Docker, Helm, PyPI) and create a full release.

### Release Types

The workflow supports three release types:

- **Release** (`release`):
  - Full release with all artifacts
  - Publishes to PyPI (production)
  - Creates Git tag
  - Creates GitHub Release with release notes from `CHANGELOG.md`
  - Docker images tagged with version and `latest`

- **Pre-release** (`pre-release`):
  - Release candidate (e.g., `0.1.0-rc.1`)
  - Publishes to all repositories (PyPI, Docker, Helm)
  - Does not create Git tag or GitHub Release
  - Useful for testing release candidates

- **Test** (`test`):
  - Test build (e.g., `0.1.0-test`)
  - Publishes to TestPyPI (not production PyPI)
  - Publishes Docker images with test tags
  - Publishes Helm Chart
  - Does not create Git tag or GitHub Release
  - Useful for testing the release process

### Artifact Locations

After a successful release:

- **Docker Image**: `ghcr.io/maskshell/cloud-cert-renewer:{version}`
  - Multi-architecture support: amd64 and arm64
  - The image manifest automatically selects the correct architecture for your platform
- **Helm Chart**: `https://maskshell.github.io/cloud-cert-renewer/charts`
- **PyPI Package**: `https://pypi.org/project/cloud-cert-renewer/`

### Version Management

The release workflow automatically synchronizes versions across all files:

- `pyproject.toml` - Python package version
- `cloud_cert_renewer/__init__.py` - `__version__`
- `helm/cloud-cert-renewer/Chart.yaml` - `version` and `appVersion`
- `CHANGELOG.md` - Version entry (when using `update_version.sh` script)
- `uv.lock` - Package version in lock file (when using `update_version.sh` script)

**Note:** The `uv.lock` file uses PEP 440 version format (e.g., `0.2.3b1` for `0.2.3-beta1`), which is the standard format for Python packages. This is automatically handled by `uv lock`.

**Automatic Version Synchronization:**

- When using manual workflow dispatch with a version specified, the workflow updates all files
- When pushing a Git tag, the workflow extracts the version and updates all files
- Version consistency is verified before proceeding with the release

**Manual Version Update:**
You can use the helper script to update versions locally before committing:

```bash
./scripts/update_version.sh 0.1.0
```

This script:

- Updates versions in all three files (`pyproject.toml`, `__init__.py`, `Chart.yaml`)
- Updates `CHANGELOG.md` (replaces `[Unreleased]` with version and date, adds new `[Unreleased]` section)
- Updates `uv.lock` (synchronizes lock file with new package version)
- Validates version consistency
- Supports semantic versioning (e.g., `0.1.0`, `0.1.0-rc.1`, `0.1.0-test`)

**Note:** The `uv.lock` file records the exact version of your package when installed in editable mode. It should be updated whenever the package version changes to ensure consistency across environments. The script automatically runs `uv lock` to update the lock file.

### CHANGELOG Update Workflow

The project follows the [Keep a Changelog](https://keepachangelog.com/) standard format.

#### CHANGELOG Format

The `CHANGELOG.md` file uses the following format:

```markdown
## [Unreleased]

### Added

- (New features to be released)

### Changed

- (Changes to be released)

## [0.2.3-beta1] - 2025-12-16

### Changed

- Actual release notes...
```

#### Updating CHANGELOG During Development

**For AI Agents and Developers:**

1. **Add changes to `[Unreleased]` section**: When making changes, add them to the `[Unreleased]` section at the top of `CHANGELOG.md`
2. **Follow Keep a Changelog format**: Use standard categories (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`)
3. **Keep entries clear and concise**: Write user-facing descriptions, not technical implementation details

**Example:**

```markdown
## [Unreleased]

### Added

- Support for YAML list format in Helm Chart `cdn.domainName` configuration

### Fixed

- Fixed certificate fingerprint comparison to handle API format variations
```

#### Releasing a Version

When releasing a version, use the `update_version.sh` script:

```bash
./scripts/update_version.sh 0.2.4
```

The script will:

1. **Update version files**: `pyproject.toml`, `__init__.py`, `Chart.yaml`
2. **Update CHANGELOG.md**:
   - Replace `## [Unreleased]` with `## [0.2.4] - YYYY-MM-DD` (using current date)
   - Add a new `## [Unreleased]` section at the top for future changes
3. **Verify version consistency**: Ensure all files have the same version

**Note:** If `CHANGELOG.md` doesn't have an `[Unreleased]` section, the script will skip CHANGELOG updates and show a warning.

#### GitHub Release Notes Extraction

The GitHub Actions release workflow automatically extracts release notes from `CHANGELOG.md`:

- **Extraction**: The workflow extracts content from the version entry (e.g., `## [0.2.4] - 2025-12-16`) up to the next version entry
- **Inclusion**: All subsections (`### Added`, `### Changed`, etc.) and their content are included
- **Fallback**: If extraction fails, a simple "Release {VERSION}" message is used

The extracted release notes are automatically included in the GitHub Release body along with artifact information.

### Manual Publishing

If you prefer to publish manually:

1. **Build Tools**: Install build and twine:

   ```bash
   uv pip install build twine
   ```

### Pre-Release Checklist

- [ ] Ensure `CHANGELOG.md` has an `[Unreleased]` section with all changes documented
- [ ] Update version using `scripts/update_version.sh <version>` (updates all files including CHANGELOG)
- [ ] Review `CHANGELOG.md` to ensure the version entry is correct and complete
- [ ] Update `[project.urls]` in `pyproject.toml` with actual repository URLs (if needed)
- [ ] Run all tests: `uv run pytest`
- [ ] Check code quality: `uv run ruff check .`
- [ ] Verify README.md renders correctly on PyPI

### Building Distribution Packages

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build
```

This creates:

- `dist/cloud-cert-renewer-<version>.tar.gz` (source distribution)
- `dist/cloud_cert_renewer-<version>-py3-none-any.whl` (wheel)

### Testing on TestPyPI

Before publishing to PyPI, test on TestPyPI:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ cloud-cert-renewer
```

### Publishing to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

You will be prompted for:

- Username: `__token__`
- Password: Your PyPI API token

### Post-Release

- [ ] Verify package on PyPI: `https://pypi.org/project/cloud-cert-renewer/`
- [ ] Create a Git tag: `git tag v0.1.0 && git push origin v0.1.0`
- [ ] Create a GitHub release with release notes from CHANGELOG.md

### Version Management

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

**Using the helper script (recommended):**

```bash
./scripts/update_version.sh 0.1.0
```

**Manual update:**

If you prefer to update versions manually:

1. `pyproject.toml` - `version = "x.y.z"`
2. `cloud_cert_renewer/__init__.py` - `__version__ = "x.y.z"`
3. `helm/cloud-cert-renewer/Chart.yaml` - `version: x.y.z` and `appVersion: "x.y.z"`
4. `CHANGELOG.md` - Replace `## [Unreleased]` with `## [x.y.z] - YYYY-MM-DD` and add new `## [Unreleased]` section
5. `uv.lock` - Run `uv lock` to update the lock file with the new package version

**Note:** Using `scripts/update_version.sh` is recommended as it handles all files automatically and ensures consistency. The script automatically runs `uv lock` to update the lock file.

### Release Checklist

Before creating a release:

- [ ] Ensure `CHANGELOG.md` has an `[Unreleased]` section with all changes documented
- [ ] Update version in all files using `scripts/update_version.sh <version>` (handles CHANGELOG automatically)
- [ ] Review the updated `CHANGELOG.md` to ensure version entry is correct
- [ ] Run all tests: `uv run pytest`
- [ ] Check code quality: `uv run ruff check .`
- [ ] Verify README.md renders correctly
- [ ] Commit version changes and CHANGELOG updates
- [ ] Push commits to main branch
- [ ] Create release via GitHub Actions (manual) or push Git tag (automatic)

**For Manual Release:**

- Go to Actions → Release → Run workflow
- Select release type and configure options
- Monitor workflow execution

**For Automatic Release:**

- Create and push Git tag: `git tag v0.1.0 && git push origin v0.1.0`
- Workflow will automatically handle the rest

## Code Structure

```text
cloud-cert-renewer/
├── main.py                    # Main program entry point
├── cloud_cert_renewer/        # Core functionality module
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Module entry point (python -m cloud_cert_renewer)
│   ├── cli.py                 # CLI argument parsing and handling
│   ├── auth/                  # Authentication module (supports multiple auth methods)
│   │   ├── base.py            # Authentication provider abstract interface
│   │   ├── access_key.py      # Access Key/Security Key authentication provider
│   │   ├── sts.py             # STS temporary credentials authentication provider
│   │   ├── iam_role.py        # IAM Role authentication provider
│   │   ├── oidc.py            # OIDC (RRSA) authentication provider for Kubernetes
│   │   ├── service_account.py # ServiceAccount authentication provider
│   │   ├── env.py             # Environment variable authentication provider
│   │   ├── errors.py          # Authentication-specific errors
│   │   └── factory.py         # Authentication provider factory
│   ├── cert_renewer/          # Certificate renewer module (Strategy pattern)
│   │   ├── base.py            # Abstract base class (Template Method pattern)
│   │   ├── cdn_renewer.py     # CDN certificate renewal strategy
│   │   ├── load_balancer_renewer.py # Load Balancer certificate renewal strategy
│   │   ├── composite.py       # Composite renewer (multiple renewers)
│   │   └── factory.py        # Certificate renewer factory
│   ├── clients/               # Client module
│   │   └── alibaba.py        # Alibaba Cloud client wrapper
│   ├── config/                # Configuration module
│   │   ├── models.py          # Configuration data classes
│   │   └── loader.py          # Configuration loader
│   ├── providers/             # Cloud service provider adapters (Adapter pattern)
│   │   ├── base.py            # Cloud service adapter interface
│   │   ├── alibaba.py         # Alibaba Cloud adapter
│   │   ├── aws.py             # AWS adapter (reserved)
│   │   ├── azure.py           # Azure adapter (reserved)
│   │   └── noop.py            # No-op adapter (for testing)
│   ├── webhook/               # Webhook notification module
│   │   ├── client.py          # Webhook HTTP client
│   │   ├── events.py          # Webhook event definitions
│   │   └── exceptions.py     # Webhook-specific exceptions
│   ├── utils/                 # Utility module
│   │   └── ssl_cert_parser.py # SSL certificate parsing and validation utility
│   ├── container.py           # Dependency injection container
│   ├── errors.py              # Common error classes
│   ├── logging_utils.py       # Logging configuration utilities
│   ├── config.py              # Backward compatibility imports
│   ├── renewer.py             # Backward compatibility imports
│   ├── adapters.py            # Backward compatibility imports
│   └── auth.py                # Backward compatibility imports
├── tests/                     # Test files (organized by design patterns)
│   ├── __init__.py
│   ├── test_clients.py         # Cloud client tests (Alibaba Cloud SDK)
│   ├── test_config.py          # Configuration loading tests
│   ├── test_utils.py           # Utility function tests (SSL certificate parser)
│   ├── test_cli.py             # CLI tests
│   ├── test_cli_smoke.py       # CLI smoke tests
│   ├── test_cert_renewer_factory.py # CertRenewerFactory tests (Factory Pattern)
│   ├── test_cert_renewer_strategy.py # CertRenewerStrategy tests (Strategy Pattern)
│   ├── test_cert_renewer_base.py # BaseCertRenewer tests (Template Method Pattern)
│   ├── test_auth_factory.py    # CredentialProviderFactory tests (Auth Factory Pattern)
│   ├── test_auth_providers.py  # CredentialProvider tests (Auth Strategy Pattern)
│   ├── test_auth_oidc.py       # OIDC authentication tests
│   ├── test_providers_adapter.py # CloudAdapter tests (Adapter Pattern)
│   ├── test_container.py       # DIContainer tests (Dependency Injection)
│   ├── test_integration.py     # Integration tests (end-to-end flows)
│   └── test_webhook/           # Webhook module tests
│       ├── test_client.py      # Webhook client tests
│       ├── test_events.py      # Webhook event tests
│       ├── test_integration.py # Webhook integration tests
│       └── test_service.py     # Webhook service tests
├── docs/                      # Documentation
│   └── webhook-configuration.md # Webhook configuration guide
├── scripts/                    # Utility scripts
│   ├── update_version.sh      # Version synchronization script
│   └── check_language.sh      # Language validation script
├── k8s/                       # Kubernetes native deployment configuration
│   └── deployment.yaml        # Deployment configuration
├── helm/                      # Helm Chart
│   └── cloud-cert-renewer/
│       ├── Chart.yaml         # Chart metadata
│       ├── values.yaml         # Default configuration values
│       ├── values-cdn.yaml    # CDN example configuration
│       ├── values-slb.yaml    # SLB example configuration
│       ├── values-webhook-example.yaml    # Webhook example configuration
│       ├── values-webhook-secret.yaml     # Webhook secret example configuration
│       └── templates/         # Kubernetes resource templates
│           ├── _helpers.tpl   # Helper templates
│           ├── deployment.yaml
│           ├── serviceaccount.yaml
│           └── webhook-secret.yaml
├── Dockerfile                 # Docker image build file
├── .env.example               # Environment variable configuration example
├── pyproject.toml             # Project configuration and dependencies (using uv)
├── CHANGELOG.md               # Changelog (Keep a Changelog format)
└── README.md                  # Project documentation
```

## Local GitHub Actions Workflow Testing

You can test GitHub Actions workflows locally using [act](https://github.com/nektos/act), which runs your workflows in Docker containers.

### Prerequisites

Install `act`:

```bash
# macOS
brew install act

# Linux (using the install script)
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Or download from releases: https://github.com/nektos/act/releases
```

### Setup

1. **Create secrets file** (optional, for workflows that need secrets):

```bash
cp .secrets.example .secrets
# Edit .secrets and fill in your values
```

**Note:** The `.secrets` file is in `.gitignore` and should NOT be committed to version control.

2. **Configure act** (optional):

The project includes a `.actrc` configuration file with recommended settings. You can modify it if needed.

### Usage

**Test a specific workflow:**

```bash
# Test the release workflow
./scripts/test-workflow.sh .github/workflows/release.yml

# Test a specific job
./scripts/test-workflow.sh .github/workflows/release.yml prepare

# Test the CI workflow
./scripts/test-workflow.sh .github/workflows/ci.yml
```

**Manual act commands:**

```bash
# List all workflows
act -l

# Run a specific workflow
act workflow_dispatch --workflows .github/workflows/release.yml

# Run a specific job
act workflow_dispatch --job prepare --workflows .github/workflows/release.yml

# Use secrets file
act workflow_dispatch --secret-file .secrets --workflows .github/workflows/release.yml
```

### Limitations

- **Docker-in-Docker**: Some workflows that require Docker-in-Docker may not work perfectly
- **Git operations**: Some git operations may behave differently in local testing
- **External services**: Workflows that interact with external services (GitHub API, Docker Hub, PyPI) will make real API calls if secrets are provided
- **Matrix strategies**: Complex matrix strategies may need adjustment for local testing

### Troubleshooting

**Issue: act not found**

- Ensure `act` is installed and in your PATH
- Check installation: `act --version`

**Issue: Docker errors**

- Ensure Docker is running: `docker ps`
- Check Docker permissions

**Issue: Workflow fails with secret errors**

- Create `.secrets` file from `.secrets.example`
- Some workflows may work without secrets (they'll skip steps that require them)

**Issue: Workflow runs but doesn't match expected behavior**

- Check `.actrc` configuration
- Verify workflow syntax: `act -l` should list your workflows
- Use `-v` flag for verbose output: `act -v workflow_dispatch`

### Best Practices

1. **Test workflows before pushing**: Run workflows locally before committing changes
2. **Use dry-run mode**: Some workflows support dry-run mode to avoid side effects
3. **Test individual jobs**: Test specific jobs rather than entire workflows when debugging
4. **Keep secrets secure**: Never commit `.secrets` file to version control
5. **Use workflow_dispatch**: Most workflows support `workflow_dispatch` trigger for manual testing

## Design Patterns

The project follows several design patterns:

- **Factory Pattern**: `CertRenewerFactory`, `CredentialProviderFactory`
- **Strategy Pattern**: `CertRenewerStrategy` implementations, `CredentialProvider` implementations
- **Template Method Pattern**: `BaseCertRenewer`
- **Adapter Pattern**: `CloudAdapter` implementations
- **Dependency Injection**: `DIContainer`

For more details, see [testing-design-principles.mdc](testing-design-principles.mdc).
