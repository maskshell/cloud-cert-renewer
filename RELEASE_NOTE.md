# Release Candidate 0.2.0-rc1

## Features

- **CLI Enhancements**:
  - Added command-line argument support (`--help`, `--version`, `--verbose`, `--quiet`).
  - Added `--dry-run` mode for safe testing and validation without API calls.
  - Added `cloud-cert-renewer` entry point for direct CLI usage.

- **OIDC Authentication (Kubernetes RRSA)**:
  - Support for dynamic credential retrieval via OIDC tokens.
  - Automatic environment variable injection by Kubernetes Service Account.
  - Service Account configuration in Helm Chart.

- **Multi-Architecture Support**:
  - Docker images now support both `linux/amd64` and `linux/arm64`.

- **Python 3.14 Support**: verified with dedicated CI quality gates.

## Improvements

- **Security**: Tightened wildcard domain matching (RFC 6125 compliance).
- **Reliability**: Configurable SDK timeout/retry settings.
- **Testing**: Test coverage increased to 94% (total 169 tests).
- **Deployment**: Default Helm chart image updated to `ghcr.io/maskshell/cloud-cert-renewer`.

## Fixes

- Fixed DIContainer singleton semantics.
- Fixed certificate validity parsing (UTC-aware datetime).
- Fixed CloudAdapterFactory default adapter registration.

## Docker Image

```bash
docker pull ghcr.io/maskshell/cloud-cert-renewer:0.2.0-rc1
```

## Installation (TestPyPI)

```bash
pip install --index-url https://test.pypi.org/simple/ cloud-cert-renewer==0.2.0-rc1
```
