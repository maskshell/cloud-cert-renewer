# Cloud Certificate Renewer

Automated HTTPS certificate renewal tool for cloud services, supporting CDN and Load Balancer products. Currently supports Alibaba Cloud, with architecture designed for multi-cloud extension.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)

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

### Environment Variables

The project supports configuration via environment variables or `.env` files. Refer to `.env.example` to create your `.env` file.

#### Required Environment Variables

- `CLOUD_ACCESS_KEY_ID`: Cloud service AccessKey ID (new name, preferred)
- `CLOUD_ACCESS_KEY_SECRET`: Cloud service AccessKey Secret (new name, preferred)
- `SERVICE_TYPE`: Service type, options: `cdn` or `lb` (backward compatible: `slb`)

#### Optional Environment Variables

- `CLOUD_PROVIDER`: Cloud provider, options: `alibaba`, `aws`, `azure`, etc. (default: `alibaba`)
- `AUTH_METHOD`: Authentication method, options: `access_key`, `sts`, `iam_role`, `service_account`, `env` (default: `access_key`)
- `CLOUD_SECURITY_TOKEN`: STS temporary security token (optional, required when `AUTH_METHOD=sts`)
- `FORCE_UPDATE`: Force update certificate even if it's the same (default: `false`)

#### Legacy Environment Variables (Deprecated, but backward compatible)

- `ALIBABA_CLOUD_ACCESS_KEY_ID`: Alibaba Cloud AccessKey ID (legacy name, use `CLOUD_ACCESS_KEY_ID` instead)
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`: Alibaba Cloud AccessKey Secret (legacy name, use `CLOUD_ACCESS_KEY_SECRET` instead)

#### CDN Configuration (when SERVICE_TYPE=cdn)

- `CDN_DOMAIN_NAME`: CDN domain name
- `CDN_CERT`: SSL certificate content (PEM format, supports multi-line)
- `CDN_CERT_PRIVATE_KEY`: SSL certificate private key (PEM format, supports multi-line)
- `CDN_REGION`: Region (default: `cn-hangzhou`)

#### Load Balancer Configuration (when SERVICE_TYPE=lb or slb)

- `LB_INSTANCE_ID`: Load Balancer instance ID (new name, preferred)
- `LB_LISTENER_PORT`: Listener port (new name, preferred)
- `LB_CERT`: SSL certificate content (PEM format, supports multi-line) (new name, preferred)
- `LB_CERT_PRIVATE_KEY`: SSL certificate private key (PEM format, supports multi-line) (new name, preferred)
- `LB_REGION`: Region (default: `cn-hangzhou`) (new name, preferred)
- `SLB_INSTANCE_ID`: SLB instance ID (legacy name, backward compatible)
- `SLB_LISTENER_PORT`: Listener port (legacy name, backward compatible)
- `SLB_CERT`: SSL certificate content (PEM format, supports multi-line) (legacy name, backward compatible)
- `SLB_CERT_PRIVATE_KEY`: SSL certificate private key (PEM format, supports multi-line) (legacy name, backward compatible)
- `SLB_REGION`: Region (default: `cn-hangzhou`) (legacy name, backward compatible)

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

Run all tests:

```bash
# Install development dependencies (if not already installed)
uv sync --extra dev

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_main.py

# Run specific test class
uv run pytest tests/test_main.py::TestCdnCertRenewer

# Show coverage
uv run pytest --cov=. --cov-report=html
```

### Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster
- cert-manager (for automatic certificate acquisition and renewal)
- Reloader (for monitoring certificate Secret changes and triggering redeployment)

#### Deployment Methods

##### Method 1: Using Helm Chart (Recommended)

1. **Create Cloud Service Credentials Secret (using generic naming, recommended)**

```bash
# Using generic naming (recommended)
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET

# Or use legacy naming (backward compatible)
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
#   --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
```

2. **Create Certificate Secret**

Certificate Secrets are typically created automatically by cert-manager, with the following format:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cert-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded certificate>
  tls.key: <base64-encoded private key>
```

3. **Build Docker Image**

```bash
docker build -t cloud-cert-renewer:latest .
```

4. **Deploy with Helm**

```bash
# Deploy with default configuration (CDN)
helm install cloud-cert-renewer ./helm/cloud-cert-renewer

# Deploy with custom configuration
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=example.com \
  --set image.tag=latest

# Deploy using example values file
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-cdn.yaml
```

##### Method 2: Using Native Kubernetes YAML

1. **Create Cloud Service Credentials Secret (using generic naming, recommended)**

```bash
# Using generic naming (recommended)
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET

# Or use legacy naming (backward compatible)
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
#   --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
```

2. **Create Certificate Secret**

Certificate Secrets are typically created automatically by cert-manager.

3. **Build Docker Image**

```bash
docker build -t cloud-cert-renewer:latest .
```

4. **Deploy Application**

Modify the configuration in `k8s/deployment.yaml`, then deploy:

```bash
kubectl apply -f k8s/deployment.yaml
```

#### Reloader Configuration

The Deployment is configured with Reloader annotations. When the `cert-secret` Secret changes, it automatically triggers Deployment redeployment, and the init container will execute certificate renewal.

#### How It Works

1. cert-manager automatically acquires/updates Let's Encrypt certificates and updates the `cert-secret` Secret
2. Reloader detects Secret changes and triggers Deployment redeployment
3. Init container starts, reads certificate from Secret, and calls cloud service API to update certificate
4. Init container exits after completion
5. Main container (placeholder) keeps running to ensure Deployment status is normal

#### Helm Chart Detailed Usage

**View all configurable parameters:**

```bash
helm show values ./helm/cloud-cert-renewer
```

**Using example values files:**

```bash
# CDN certificate renewal
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-cdn.yaml

# Load Balancer certificate renewal
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-slb.yaml
```

**Upgrade deployment:**

```bash
# Upgrade to new version
helm upgrade cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set image.tag=v0.2.0

# Upgrade and modify configuration
helm upgrade cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set cdn.domainName=new-domain.com
```

**Validate template rendering:**

```bash
# View rendered YAML (without actual deployment)
helm template cloud-cert-renewer ./helm/cloud-cert-renewer

# View with custom values
helm template cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-cdn.yaml
```

**Check Chart:**

```bash
helm lint ./helm/cloud-cert-renewer
```

## Existing Environment

Let's Encrypt SSL certificates currently use Kubernetes-deployed `cert-manager` for automatic acquisition and renewal.

The "[stakater/Reloader](https://github.com/stakater/Reloader)" application is deployed. By adding specific annotations to the Deployment, it can track changes to a ConfigMap/Secret. When a ConfigMap/Secret changes, it can automatically redeploy (e.g., Rollout Restart) the Deployment.

## Design Approach

Create a Deployment with two containers: one init container and one nominal main container.

1. **Main Container**: The main container is a placeholder application (busybox), used only as a placeholder and not actually used.
2. **Init Container**: The init container responds to the aforementioned Reloader, retrieves the certificate secret, and calls the cloud service API to update the certificate for the corresponding product (Load Balancer instance or CDN instance).

The certificate renewal action is placed in the init container because the main container has a long lifecycle, while the init container is one-time and can exit after completion. The main container needs to keep running to ensure the Deployment does not enter a failed state.

Each SLB instance or CDN instance requires a corresponding Deployment for certificate renewal.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Language Policy

**All project content must be in English:**
- Code comments, docstrings, documentation, commit messages, and error messages should be in English
- See [CONTRIBUTING.md](CONTRIBUTING.md) for full language policy and exceptions

## Development

### Environment Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies and development dependencies
uv sync --extra dev
```

### Code Formatting

```bash
# Format code with ruff
uv run ruff format .

# Format code with black
uv run black .

# Check code format (without modification)
uv run black . --check
```

### Code Linting

```bash
# Lint check with ruff
uv run ruff check .

# Auto-fix issues with ruff
uv run ruff check . --fix
```

### YAML File Formatting

The project is configured with `yamllint` and `pre-commit` for YAML file checking and formatting.

**Using yamllint to check YAML files:**

```bash
# Check all YAML files
uv run yamllint .

# Check specific file
uv run yamllint k8s/deployment.yaml

# Check and auto-fix (some issues)
uv run yamllint --format parsable k8s/deployment.yaml
```

**Using pre-commit (recommended):**

```bash
# Install pre-commit hooks (automatically run on git commit)
uv run pre-commit install

# Manually run all checks
uv run pre-commit run --all-files

# Only check YAML files
uv run pre-commit run yamllint --all-files
```

**Recommended YAML formatting tools:**

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

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with print output
uv run pytest -s

# Run specific test file
uv run pytest tests/test_main.py

# Run specific test class
uv run pytest tests/test_main.py::TestCdnCertRenewer

# Run specific test method
uv run pytest tests/test_main.py::TestCdnCertRenewer::test_create_client

# Stop at first failure
uv run pytest -x

# Show top 10 slowest tests
uv run pytest --durations=10

# Generate coverage report
uv run pytest --cov=. --cov-report=html
```

### Building Docker Image

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

### Code Structure

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
├── tests/                     # Test files
│   ├── __init__.py
│   ├── test_main.py           # Main program tests
│   └── test_ssl_cert_parser.py # SSL certificate parser tests
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

## Troubleshooting

### Common Issues

#### 1. Certificate Validation Failed

**Symptoms:** Log shows "Certificate validation failed: domain xxx is not in the certificate or certificate has expired"

**Solutions:**

- Check if the certificate contains the target domain
- Check if the certificate has expired
- Verify certificate format is correct (PEM format)
- For wildcard certificates, verify domain matching rules

#### 2. Configuration Error

**Symptoms:** Log shows "Configuration error: missing required environment variables"

**Solutions:**

- Check if all required environment variables are set
- Verify environment variable names are spelled correctly
- Check if Secret exists and contains correct keys

#### 3. API Call Failed

**Symptoms:** Log shows "CDN certificate renewal failed" or "Load Balancer certificate renewal failed"

**Solutions:**

- Check if AccessKey is correct and has appropriate permissions
- Verify region configuration is correct
- Check network connectivity
- View diagnostic URL in error message

#### 4. Kubernetes Deployment Issues

**Check Pod Status:**

```bash
# View Pod list
kubectl get pods -l app.kubernetes.io/name=cloud-cert-renewer

# View Pod details
kubectl describe pod <pod-name>

# View init container logs
kubectl logs <pod-name> -c cert-renewer

# View main container logs
kubectl logs <pod-name> -c placeholder

# View Pod events
kubectl get events --field-selector involvedObject.name=<pod-name>
```

**Check Secrets:**

```bash
# Check if Secrets exist
kubectl get secret cloud-credentials
kubectl get secret cert-secret

# View Secret content (base64 decoded)
kubectl get secret cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d
```

**Check Reloader:**

```bash
# Check if Reloader is running
kubectl get pods -n <reloader-namespace> -l app=reloader

# View Reloader logs
kubectl logs -n <reloader-namespace> <reloader-pod-name>
```

### Debugging Tips

1. **Local Test Configuration:**

   ```bash
   # Export environment variables from Kubernetes Secret for local testing
   kubectl get secret cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d > cert.pem
   kubectl get secret cert-secret -o jsonpath='{.data.tls\.key}' | base64 -d > key.pem
   ```

2. **Enable Verbose Logging:**
   The program uses Python logging, log level can be controlled via environment variables (if implemented)

3. **Verify Certificate Content:**

   ```bash
   # View certificate information
   openssl x509 -in cert.pem -text -noout

   # Check certificate expiration date
   openssl x509 -in cert.pem -noout -dates
   ```

## Notes

1. **Security**:
   - In production environments, use more secure authentication methods (such as STS) instead of directly using AccessKey
   - Do not hardcode sensitive information in code
   - Use Kubernetes Secrets to manage sensitive data

2. **Certificate Format**:
   - Ensure certificate and private key formats are correct, use PEM format
   - Certificate chain should include complete chain (server certificate + intermediate certificate + root certificate)
   - Private key format should be RSA or ECDSA

3. **Region Configuration**:
   - Configure correct region codes according to actual cloud service regions used
   - Common regions: `cn-hangzhou`, `cn-beijing`, `cn-shanghai`, `cn-shenzhen`, etc.

4. **Error Handling**:
   - The program logs detailed information for troubleshooting
   - Recommend configuring log collection systems (such as ELK, Loki) for centralized management

5. **Resource Limits**:
   - Adjust resource requests and limits according to actual load
   - Init container execution time is usually short, but sufficient resources are needed to complete API calls

6. **Multi-Instance Deployment**:
   - Each CDN domain or Load Balancer instance requires a separate Deployment for certificate renewal
   - Use different release names or namespaces for distinction

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork this project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Standards

- Use `black` to format code
- Use `ruff` for code linting
- Write unit tests
- Update relevant documentation
