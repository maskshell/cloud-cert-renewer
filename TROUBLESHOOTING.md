# Troubleshooting Guide

This document provides solutions to common issues and debugging tips for the Cloud Certificate Renewer.

## Table of Contents

- [Common Issues](#common-issues)
- [Debugging Tips](#debugging-tips)
- [Best Practices](#best-practices)

## Common Issues

### 1. Certificate Validation Failed

**Symptoms:** Log shows "Certificate validation failed: domain xxx is not in the certificate or certificate has expired"

**Solutions:**

- Check if the certificate contains the target domain
- Check if the certificate has expired
- Verify certificate format is correct (PEM format)
- For wildcard certificates, verify domain matching rules

### 2. Configuration Error

**Symptoms:** Log shows "Configuration error: missing required environment variables"

**Solutions:**

- Check if all required environment variables are set
- Verify environment variable names are spelled correctly
- Check if Secret exists and contains correct keys
- Refer to `.env.example` for the correct variable names

### 3. API Call Failed

**Symptoms:** Log shows "CDN certificate renewal failed" or "Load Balancer certificate renewal failed"

**Solutions:**

- Check if AccessKey is correct and has appropriate permissions
- Verify region configuration is correct
- Check network connectivity
- View diagnostic URL in error message
- For STS authentication, verify the security token is valid and not expired

### 4. Kubernetes Deployment Issues

#### Check Pod Status

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

#### Check Secrets

```bash
# Check if Secrets exist
kubectl get secret cloud-credentials
kubectl get secret cert-secret

# View Secret content (base64 decoded)
kubectl get secret cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d

# View Secret keys
kubectl get secret cloud-credentials -o jsonpath='{.data}' | jq 'keys'
```

#### Check Reloader

```bash
# Check if Reloader is running
kubectl get pods -n <reloader-namespace> -l app=reloader

# View Reloader logs
kubectl logs -n <reloader-namespace> <reloader-pod-name>

# Check Reloader configuration
kubectl get deployment <deployment-name> -o yaml | grep -A 5 reloader
```

#### Common Kubernetes Issues

- **Init container fails**: Check logs, verify Secrets are correctly mounted, verify network connectivity to cloud API
- **Secret not found**: Ensure Secrets are created in the correct namespace
- **Reloader not triggering**: Verify Reloader annotations are correct, check Reloader pod status
- **Certificate not updating**: Check if cert-manager is updating the Secret, verify Reloader is detecting changes

## Debugging Tips

### 1. Local Test Configuration

```bash
# Export environment variables from Kubernetes Secret for local testing
kubectl get secret cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d > cert.pem
kubectl get secret cert-secret -o jsonpath='{.data.tls\.key}' | base64 -d > key.pem

# Export credentials from Secret
kubectl get secret cloud-credentials -o jsonpath='{.data.access-key-id}' | base64 -d
kubectl get secret cloud-credentials -o jsonpath='{.data.access-key-secret}' | base64 -d
```

### 2. Enable Verbose Logging

The program uses Python logging. Log level can be controlled via environment variables (if implemented) or by modifying the logging configuration in the code.

### 3. Verify Certificate Content

```bash
# View certificate information
openssl x509 -in cert.pem -text -noout

# Check certificate expiration date
openssl x509 -in cert.pem -noout -dates

# Check certificate subject and SAN
openssl x509 -in cert.pem -noout -subject -ext subjectAltName

# Verify certificate and private key match
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5
# These two hashes should match
```

### 4. Test Cloud API Connectivity

```bash
# Test Alibaba Cloud API connectivity (if using Alibaba Cloud)
# You can use the Alibaba Cloud CLI or test with curl
curl -X GET "https://cdn.aliyuncs.com/?Action=DescribeCdnDomainConfigs" \
  -H "Authorization: ..."
```

### 5. Validate Configuration

```bash
# Run with dry-run mode (if implemented)
uv run python main.py --dry-run

# Validate configuration without executing
uv run python -c "from cloud_cert_renewer.config import load_config; print(load_config())"
```

## Best Practices

### Security

- In production environments, use more secure authentication methods (such as STS) instead of directly using AccessKey
- Do not hardcode sensitive information in code
- Use Kubernetes Secrets to manage sensitive data
- Rotate credentials regularly
- Use least privilege principle for IAM permissions

### Certificate Format

- Ensure certificate and private key formats are correct, use PEM format
- Certificate chain should include complete chain (server certificate + intermediate certificate + root certificate)
- Private key format should be RSA or ECDSA
- Verify certificate and private key match before deployment

### Region Configuration

- Configure correct region codes according to actual cloud service regions used
- Common Alibaba Cloud regions: `cn-hangzhou`, `cn-beijing`, `cn-shanghai`, `cn-shenzhen`, etc.
- Verify region availability for the specific service (CDN or Load Balancer)

### Error Handling

- The program logs detailed information for troubleshooting
- Recommend configuring log collection systems (such as ELK, Loki) for centralized management
- Set up alerts for certificate renewal failures
- Monitor certificate expiration dates proactively

### Resource Limits

- Adjust resource requests and limits according to actual load
- Init container execution time is usually short, but sufficient resources are needed to complete API calls
- Monitor resource usage and adjust as needed

### Multi-Instance Deployment

- Each CDN domain or Load Balancer instance requires a separate Deployment for certificate renewal
- Use different release names or namespaces for distinction
- Consider using Helm Chart values files for different environments

### Monitoring and Observability

- Set up monitoring for certificate renewal success/failure rates
- Monitor API call latency and error rates
- Track certificate expiration dates
- Set up alerts for renewal failures

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [README.md](README.md) for basic usage
2. Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
3. Check existing GitHub issues
4. Create a new issue with detailed information:
   - Error messages and logs
   - Configuration (with sensitive data redacted)
   - Steps to reproduce
   - Environment details (Kubernetes version, Python version, etc.)
