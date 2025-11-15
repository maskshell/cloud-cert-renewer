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
```

### Detailed Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies and development dependencies
uv sync --extra dev
```

## Configuration

The project supports configuration via environment variables or `.env` files. Refer to `.env.example` to create your `.env` file.

### Required Environment Variables

- `CLOUD_ACCESS_KEY_ID`: Cloud service AccessKey ID (new name, preferred)
- `CLOUD_ACCESS_KEY_SECRET`: Cloud service AccessKey Secret (new name, preferred)
- `SERVICE_TYPE`: Service type, options: `cdn` or `lb` (backward compatible: `slb`)

### Optional Environment Variables

- `CLOUD_PROVIDER`: Cloud provider, options: `alibaba`, `aws`, `azure`, etc. (default: `alibaba`)
- `AUTH_METHOD`: Authentication method, options: `access_key`, `sts`, `iam_role`, `service_account`, `env` (default: `access_key`)
- `CLOUD_SECURITY_TOKEN`: STS temporary security token (optional, required when `AUTH_METHOD=sts`)
- `FORCE_UPDATE`: Force update certificate even if it's the same (default: `false`)

### CDN Configuration (when SERVICE_TYPE=cdn)

- `CDN_DOMAIN_NAME`: CDN domain name
- `CDN_CERT`: SSL certificate content (PEM format, supports multi-line)
- `CDN_CERT_PRIVATE_KEY`: SSL certificate private key (PEM format, supports multi-line)
- `CDN_REGION`: Region (default: `cn-hangzhou`)

### Load Balancer Configuration (when SERVICE_TYPE=lb or slb)

- `LB_INSTANCE_ID`: Load Balancer instance ID (new name, preferred)
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
- **Load Balancer**: `slb:DescribeServerCertificates`, `slb:UploadServerCertificate`

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
uv run yamllint .

# Check specific file
uv run yamllint k8s/deployment.yaml

# Check and auto-fix (some issues)
uv run yamllint --format parsable k8s/deployment.yaml
```

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

**Note:** The GitHub Actions release workflow automatically builds and publishes multi-architecture images (amd64 and arm64) to GitHub Container Registry. No manual multi-architecture build is required for releases.

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

- Updates versions in all three files
- Validates version consistency
- Supports semantic versioning (e.g., `0.1.0`, `0.1.0-rc.1`, `0.1.0-test`)

### Manual Publishing

If you prefer to publish manually:

1. **Build Tools**: Install build and twine:

   ```bash
   uv pip install build twine
   ```

### Pre-Release Checklist

- [ ] Update version in `pyproject.toml` and `cloud_cert_renewer/__init__.py`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Update `[project.urls]` in `pyproject.toml` with actual repository URLs
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

Update version in:

1. `pyproject.toml` - `version = "x.y.z"`
2. `cloud_cert_renewer/__init__.py` - `__version__ = "x.y.z"`
3. `helm/cloud-cert-renewer/Chart.yaml` - `version: x.y.z` and `appVersion: "x.y.z"`
4. `CHANGELOG.md` - Add new version entry

### Release Checklist

Before creating a release:

- [ ] Update version in all files (or use `scripts/update_version.sh`)
- [ ] Update `CHANGELOG.md` with release notes (format: `## [version]`)
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
│   ├── auth/                  # Authentication module (supports multiple auth methods)
│   │   ├── base.py            # Authentication provider abstract interface
│   │   ├── access_key.py      # Access Key/Security Key authentication provider
│   │   ├── sts.py             # STS temporary credentials authentication provider
│   │   ├── iam_role.py        # IAM Role authentication provider
│   │   ├── service_account.py # ServiceAccount authentication provider
│   │   ├── env.py             # Environment variable authentication provider
│   │   └── factory.py         # Authentication provider factory
│   ├── cert_renewer/          # Certificate renewer module (Strategy pattern)
│   │   ├── base.py            # Abstract base class (Template Method pattern)
│   │   ├── cdn_renewer.py     # CDN certificate renewal strategy
│   │   ├── load_balancer_renewer.py # Load Balancer certificate renewal strategy
│   │   └── factory.py         # Certificate renewer factory
│   ├── clients/               # Client module
│   │   └── alibaba.py        # Alibaba Cloud client wrapper
│   ├── config/                # Configuration module
│   │   ├── models.py          # Configuration data classes
│   │   └── loader.py          # Configuration loader
│   ├── providers/             # Cloud service provider adapters (Adapter pattern)
│   │   ├── base.py            # Cloud service adapter interface
│   │   ├── alibaba.py         # Alibaba Cloud adapter
│   │   ├── aws.py             # AWS adapter (reserved)
│   │   └── azure.py           # Azure adapter (reserved)
│   ├── utils/                 # Utility module
│   │   └── ssl_cert_parser.py # SSL certificate parsing and validation utility
│   ├── container.py           # Dependency injection container
│   ├── config.py              # Backward compatibility imports
│   ├── renewer.py             # Backward compatibility imports
│   └── adapters.py            # Backward compatibility imports
├── tests/                     # Test files (organized by design patterns)
│   ├── __init__.py
│   ├── test_clients.py         # Cloud client tests (Alibaba Cloud SDK)
│   ├── test_config.py          # Configuration loading tests
│   ├── test_utils.py           # Utility function tests (SSL certificate parser)
│   ├── test_cert_renewer_factory.py # CertRenewerFactory tests (Factory Pattern)
│   ├── test_cert_renewer_strategy.py # CertRenewerStrategy tests (Strategy Pattern)
│   ├── test_cert_renewer_base.py # BaseCertRenewer tests (Template Method Pattern)
│   ├── test_auth_factory.py    # CredentialProviderFactory tests (Auth Factory Pattern)
│   ├── test_auth_providers.py  # CredentialProvider tests (Auth Strategy Pattern)
│   ├── test_providers_adapter.py # CloudAdapter tests (Adapter Pattern)
│   ├── test_container.py       # DIContainer tests (Dependency Injection)
│   └── test_integration.py     # Integration tests (end-to-end flows)
├── k8s/                       # Kubernetes native deployment configuration
│   └── deployment.yaml        # Deployment configuration
├── helm/                      # Helm Chart
│   └── cloud-cert-renewer/
│       ├── Chart.yaml         # Chart metadata
│       ├── values.yaml        # Default configuration values
│       ├── values-cdn.yaml    # CDN example configuration
│       ├── values-slb.yaml    # SLB example configuration
│       └── templates/         # Kubernetes resource templates
│           ├── _helpers.tpl   # Helper templates
│           └── deployment.yaml
├── Dockerfile                 # Docker image build file
├── .env.example               # Environment variable configuration example
├── pyproject.toml             # Project configuration and dependencies (using uv)
└── README.md                  # Project documentation
```

## Design Patterns

The project follows several design patterns:

- **Factory Pattern**: `CertRenewerFactory`, `CredentialProviderFactory`
- **Strategy Pattern**: `CertRenewerStrategy` implementations, `CredentialProvider` implementations
- **Template Method Pattern**: `BaseCertRenewer`
- **Adapter Pattern**: `CloudAdapter` implementations
- **Dependency Injection**: `DIContainer`

For more details, see [testing-design-principles.mdc](testing-design-principles.mdc).
