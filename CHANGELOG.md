# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
