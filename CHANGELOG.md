# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- OIDC (OpenID Connect) authentication support for Kubernetes RRSA (RAM Role for Service Account)
  - Support for dynamic credential retrieval via OIDC tokens
  - Automatic environment variable injection by Kubernetes Service Account
  - Service Account configuration in Helm Chart
  - Conditional environment variable setup (access_key not required for OIDC)

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
