# Development Guide

This document provides detailed information for developers working on the Cloud Certificate Renewer project.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Code Formatting](#code-formatting)
- [Code Linting](#code-linting)
- [YAML File Formatting](#yaml-file-formatting)
- [Test Execution](#test-execution)
- [Building Docker Image](#building-docker-image)
- [Code Structure](#code-structure)

## Environment Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies and development dependencies
uv sync --extra dev
```

## Code Formatting

```bash
# Format code with ruff
uv run ruff format .

# Format code with black
uv run black .

# Check code format (without modification)
uv run black . --check
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

```bash
# Install pre-commit hooks (automatically run on git commit)
uv run pre-commit install

# Manually run all checks
uv run pre-commit run --all-files

# Only check YAML files
uv run pre-commit run yamllint --all-files
```

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

```bash
# Build image
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

## Code Structure

```
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

