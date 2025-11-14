# Cloud Certificate Renewer

Automated HTTPS certificate renewal tool for cloud services, supporting CDN and Load Balancer products. Currently supports Alibaba Cloud, with architecture designed for multi-cloud extension.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)

## Features

- Automatic certificate renewal for cloud CDN services (currently supports Alibaba Cloud)
- Automatic certificate renewal for cloud Load Balancer services (currently supports Alibaba Cloud SLB)
- Certificate validation (domain matching, expiration checking)
- Support for wildcard domain certificates
- Configuration via environment variables or Kubernetes Secrets
- Comprehensive error handling and logging
- Helm Chart deployment support
- Integration with cert-manager and Reloader

## Quick Start

### Local Quick Test

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

### Kubernetes Quick Deployment

```bash
# 1. Create Secret (using generic naming, recommended)
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_KEY \
  --from-literal=access-key-secret=YOUR_SECRET

# Or use legacy naming (backward compatible)
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_KEY \
#   --from-literal=access-key-secret=YOUR_SECRET

# 2. Deploy using Helm
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=your-domain.com
```

For detailed Kubernetes deployment instructions, see [Helm Chart README](helm/cloud-cert-renewer/README.md).

## Requirements

- Python 3.8+
- uv (Python package manager)

## Installation

### Install Dependencies with uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
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

## Usage

### Local Execution

1. Create `.env` file (refer to `.env.example`)

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and configure necessary environment variables

3. Run the program:

   ```bash
   uv run python main.py
   ```

### Running Tests

```bash
# Install development dependencies (if not already installed)
uv sync --extra dev

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Show coverage
uv run pytest --cov=. --cov-report=html
```

For detailed testing information, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- cert-manager (for automatic certificate acquisition and renewal)
- Reloader (for monitoring certificate Secret changes and triggering redeployment)

### Quick Deployment

See [Quick Start](#kubernetes-quick-deployment) section above.

### Deployment Methods

#### Method 1: Using Helm Chart (Recommended)

See [Helm Chart README](helm/cloud-cert-renewer/README.md) for detailed instructions.

#### Method 2: Using Native Kubernetes YAML

1. Create Cloud Service Credentials Secret
2. Create Certificate Secret (typically via cert-manager)
3. Build Docker Image
4. Modify `k8s/deployment.yaml` and deploy:

   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

### How It Works

1. cert-manager automatically acquires/updates Let's Encrypt certificates and updates the `cert-secret` Secret
2. Reloader detects Secret changes and triggers Deployment redeployment
3. Init container starts, reads certificate from Secret, and calls cloud service API to update certificate
4. Init container exits after completion
5. Main container (placeholder) keeps running to ensure Deployment status is normal

For detailed deployment instructions and troubleshooting, see:

- [Helm Chart README](helm/cloud-cert-renewer/README.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guidelines for contributing to the project
- **[DEVELOPMENT.md](DEVELOPMENT.md)**: Detailed development guide (code formatting, linting, testing, building)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Common issues and debugging tips
- **[Helm Chart README](helm/cloud-cert-renewer/README.md)**: Detailed Kubernetes deployment guide
- **[testing-design-principles.mdc](testing-design-principles.mdc)**: Testing design and implementation principles

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Language Policy

**All project content must be in English:**

- Code comments, docstrings, documentation, commit messages, and error messages should be in English
- See [CONTRIBUTING.md](CONTRIBUTING.md) for full language policy and exceptions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
