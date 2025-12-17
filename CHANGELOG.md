# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.8-beta3] - 2025-12-17

### Added

- CI/CD release workflow enhancements:
  - Added source code archive generation for GitHub releases (`.tar.gz` format)
  - Added SHA256 checksums file generation for all release artifacts (source archive and Helm chart)
  - Added chart file filtering to ensure only the current version's chart is included in releases
  - Improved release artifact organization with explicit file paths

### Improved

- CI/CD release workflow reliability:
  - Added chart directory cleanup step before downloading artifacts
  - Enhanced chart file filtering with fallback logic for better error handling
  - Release artifacts now include source code archive and checksums for verification

## [0.2.8-beta2] - 2025-12-17

### Improved

- Webhook event handling:
  - Added support for 'all' keyword in `enabled_events` to enable all event types at once
  - Added INFO-level logging when webhook is triggered, including event type and event ID for better observability

## [0.2.8-beta1] - 2025-12-17

### Added

- Webhook builders and formatters with WeChat Work support:
  - Added webhook builder pattern with WeChat Work implementation for flexible webhook client creation
  - Added webhook formatter pattern with base, generic, and WeChat Work formatters for customizable message formatting
  - Updated configuration loader to support webhook builder and formatter selection via environment variables
  - Added comprehensive tests for builders and formatters (100% coverage)
  - Backward compatible with existing webhook configuration
- Webhook diagnostic and troubleshooting tools:
  - Added `scripts/check-webhook-secret.sh` script to verify webhook secret existence and configuration
  - Added `scripts/diagnose-webhook.sh` comprehensive diagnostic script for webhook configuration issues
  - Added detailed webhook troubleshooting section to TROUBLESHOOTING.md with step-by-step solutions

### Improved

- Webhook configuration logging:
  - Added logging when webhook URL is found or not found during configuration loading
  - Added logging for webhook service initialization status with URL and enabled events information
  - Improved debug logging for webhook configuration troubleshooting

## [0.2.7-beta1] - 2025-12-16

### Added

- Local GitHub Actions workflow testing support:
  - Added `act` configuration file (`.actrc`) for local workflow testing
  - Added `.secrets.example` template for local testing secrets
  - Added `scripts/test-workflow.sh` helper script for testing workflows locally
  - Added `scripts/test-workflow-output.sh` test script for verifying GitHub Actions output handling
  - Added documentation section in DEVELOPMENT.md for local workflow testing with act
  - Added `.secrets` to `.gitignore` to prevent committing local testing secrets

### Fixed

- CI/CD workflow improvements:
  - Improved heredoc delimiter handling in release workflow by using unique delimiter (`CUSTOM_SECTION_EOF`) to avoid conflicts with content

## [0.2.6-beta6] - 2025-12-16

### Fixed

- CI/CD workflow improvements:
  - Fixed multi-line custom section handling in release workflow by writing content to temporary file before outputting to GITHUB_OUTPUT, ensuring proper formatting of the CUSTOM_SECTION variable

## [0.2.6-beta5] - 2025-12-16

### Fixed

- Webhook handling improvements:
  - Fixed potential race condition in batch webhook summary by adding delay to ensure individual webhook threads are queued before sending batch summary
  - Simplified webhook threading by relying on `WebhookService.send_event()` internal threading instead of manual thread creation

## [0.2.6-beta4] - 2025-12-16

### Added

- CI/CD workflow enhancements:
  - Added support for custom container registry publishing alongside GitHub Container Registry and Docker Hub
  - Conditional login to custom registry when `CUSTOM_REGISTRY_URL` secret is configured
  - Automatic inclusion of custom registry images in multi-architecture builds
  - Custom registry information included in release notes and publish summaries

## [0.2.6-beta3] - 2025-12-16

### Fixed

- CI/CD workflow improvements:
  - Fixed Docker Hub description update "Forbidden" error by making the step non-blocking (`continue-on-error: true`)
  - Updated documentation to clarify Docker Hub token requires `Read, Write & Delete` permissions (not just Read & Write)
  - Added workflow comments explaining token permission requirements

## [0.2.6-beta2] - 2025-12-16

### Fixed

- Docker image build fixes:
  - Fixed `OSError: Readme file does not exist: README.md` during Docker build by adding `COPY README.md ./` to Dockerfile (required by `pyproject.toml` readme field)
  - Fixed `useradd warning: appuser's uid 1000 is greater than SYS_UID_MAX 999` by changing UID/GID from 1000 to 999

### Added

- CI/CD workflow enhancements:
  - Added automatic Docker Hub description update from README.md using `peter-evans/dockerhub-description` action
  - Docker Hub repository description now automatically syncs with README.md on each release

## [0.2.6-beta1] - 2025-12-16

### Changed

- Docker image optimizations:
  - Added `.dockerignore` to exclude non-runtime files (tests, docs, CI/CD configs)
  - Removed `README.md` from Docker image to reduce size
  - Optimized Dockerfile with cache cleanup (Python cache, uv cache, apt cache)
  - Merged RUN commands to reduce image layers
  - Image size reduction expected: 30-50%

### Security

- Docker image security improvements:
  - Added non-root user (`appuser` with UID/GID 1000) to run the application
  - Enabled supply chain attestations (SBOM and Provenance) in CI/CD workflow
  - Resolves Docker Hub security warnings for non-root user and missing attestations

## [0.2.5-beta1] - 2025-12-16

### Added

- Docker Hub multi-architecture image publishing support
  - Automatic publishing to Docker Hub alongside GitHub Container Registry
  - Digest consistency between registries (same image content for each architecture)
  - Updated release workflow to support dual registry publishing

## [0.2.4-beta1] - 2025-12-16

### Added

- Helm Chart enhancements:
  - Added CI workflow for Helm chart testing (linting, template rendering, dependency validation, dry-run installation)
  - Added `imagePullSecrets` support for private container registries
  - Updated documentation with image pull secrets configuration examples

## [0.2.3-beta1] - 2025-12-16

### Changed

- Helm Chart `cdn.domainName` now supports YAML list format (recommended) in addition to comma-separated string (backward compatible)

## [0.2.0-rc1] - 2025-12-15

### Added

- CLI enhancements:
  - Added command-line argument support (`--help`, `--version`, `--verbose`, `--quiet`)
  - Added `--dry-run` mode for safe testing and validation without API calls
- OIDC (OpenID Connect) authentication support for Kubernetes RRSA (RAM Role for Service Account)
  - Support for dynamic credential retrieval via OIDC tokens
  - Automatic environment variable injection by Kubernetes Service Account
  - Service Account configuration in Helm Chart
  - Conditional environment variable setup (access_key not required for OIDC)
- Python 3.14 support with dedicated CI quality gates
  - Pre-commit validation under Python 3.14
  - Package build and install smoke tests
- `[project.scripts]` entry point for direct CLI usage via `cloud-cert-renewer`
- Multi-architecture Docker image support (amd64 and arm64)

### Changed

- Enhanced `CredentialProvider` Protocol with `get_credential_client()` method for type safety
- Improved certificate fingerprint comparison with normalization (handles API format variations)
- Consolidated certificate fingerprint comparison at `BaseCertRenewer` level
- Configurable SDK timeout/retry via environment variables (`CLOUD_API_CONNECT_TIMEOUT`, `CLOUD_API_READ_TIMEOUT`, `CLOUD_API_MAX_ATTEMPTS`)
- Default Helm chart image repository updated to `ghcr.io/maskshell/cloud-cert-renewer`

### Fixed

- Fixed DIContainer singleton semantics (non-singleton factories now correctly return new instances)
- Fixed certificate validity parsing to use UTC-aware datetime (removes cryptography deprecation warnings)
- Tightened wildcard domain matching to comply with RFC 6125 (single-label only)
- Fixed CloudAdapterFactory default adapter registration (custom adapters no longer prevent defaults)
- Removed unused `force` parameter from adapter/client layer

### Improved

- Test coverage increased from 80% to 94%
- Added comprehensive tests for `IAMRoleCredentialProvider` (100% coverage)
- Added comprehensive tests for `EnvCredentialProvider` (100% coverage)
- Total test count increased from ~100 to 169

## [0.1.0] - 2025-11-15

### Added

- Initial release of Cloud Certificate Renewer
- Support for Alibaba Cloud CDN certificate renewal
- Support for Alibaba Cloud SLB (Load Balancer) certificate renewal
- Certificate validation (domain matching, expiration checking)
- Support for wildcard domain certificates
- Multiple authentication methods:
  - Access Key authentication
  - STS (Security Token Service) temporary credentials
  - IAM Role authentication
  - Service Account authentication
  - Environment variable authentication
- Configuration via environment variables or `.env` files
- Comprehensive error handling and logging
- Helm Chart for Kubernetes deployment
- Integration with cert-manager and Reloader
- Design patterns implementation:
  - Factory Pattern for certificate renewers and credential providers
  - Strategy Pattern for different renewal strategies
  - Template Method Pattern for common renewal flow
  - Adapter Pattern for multi-cloud support
  - Dependency Injection container
- Comprehensive test suite with design pattern organization
- Documentation:
  - README.md with quick start guide
  - DEVELOPMENT.md with detailed development guide
  - CONTRIBUTING.md with contribution guidelines
  - TROUBLESHOOTING.md with common issues and solutions
  - Helm Chart README with deployment instructions
  - RAM permissions documentation for Alibaba Cloud
- Automated release workflow (`.github/workflows/release.yml`):
  - Unified release process for Docker images, Helm Charts, and PyPI packages
  - Multi-architecture Docker image support (amd64 and arm64)
  - Automatic version synchronization across all files
  - Support for manual and automatic (tag-based) releases
  - Release types: release, pre-release, and test builds
  - Automated GitHub Release creation with release notes from CHANGELOG.md

### Security

- Support for STS temporary credentials
- RAM permissions documentation and best practices
- Least privilege principle recommendations

[0.1.0]: https://github.com/maskshell/cloud-cert-renewer/releases/tag/v0.1.0
