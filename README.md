# Cloud Certificate Renewer

Automated HTTPS certificate renewal tool for cloud services, supporting CDN and Load Balancer products. Currently supports Alibaba Cloud, with architecture designed for multi-cloud extension.

## Table of Contents

- [Features](#features)
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
- Automated release workflow with multi-architecture Docker images, Helm Charts, and PyPI packages

## Kubernetes Deployment

### Prerequisites

**Required:**

- Kubernetes cluster

**Recommended:**

- cert-manager (for automatic certificate acquisition and renewal)
- Reloader (for monitoring certificate Secret changes and automatically triggering Deployment redeployment)

### Deployment

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

For detailed deployment instructions and troubleshooting, see:

- [Helm Chart README](helm/cloud-cert-renewer/README.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### How It Works

1. cert-manager automatically acquires/updates Let's Encrypt certificates and updates the `cert-secret` Secret
2. Reloader detects Secret changes and triggers Deployment redeployment
3. Init container starts, reads certificate from Secret, and calls cloud service API to update certificate
4. Init container exits after completion
5. Main container (placeholder) keeps running to ensure Deployment status is normal

### Development

For development and testing, see [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

## Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guidelines for contributing to the project
- **[DEVELOPMENT.md](DEVELOPMENT.md)**: Detailed development guide (code formatting, linting, testing, building)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Common issues and debugging tips
- **[Helm Chart README](helm/cloud-cert-renewer/README.md)**: Detailed Kubernetes deployment guide
- **[testing-design-principles.mdc](testing-design-principles.mdc)**: Testing design and implementation principles

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, including the language policy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
