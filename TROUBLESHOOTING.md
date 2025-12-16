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

**Possible Causes:**

- Missing required environment variables
- Incorrect environment variable names
- Secret not created or missing keys (when not using OIDC)
- Incorrect Secret key names
- OIDC authentication misconfigured (missing Service Account or RRSA annotations)

**Solutions:**

- Check if all required environment variables are set
- Verify environment variable names are spelled correctly
- Check if Secret exists and contains correct keys (only required for non-OIDC authentication)
- Refer to `.env.example` for the correct variable names
- For OIDC authentication:
  - Verify Service Account is created and configured with RRSA annotations
  - Check that `AUTH_METHOD=oidc` is set
  - Verify OIDC parameters are automatically injected by Kubernetes (ALIBABA_CLOUD_ROLE_ARN, ALIBABA_CLOUD_OIDC_PROVIDER_ARN, ALIBABA_CLOUD_OIDC_TOKEN_FILE)

### 3. API Call Failed

**Symptoms:** Log shows "CDN certificate renewal failed" or "Load Balancer certificate renewal failed"

**Possible Causes:**

- Invalid AccessKey ID or Secret (for access_key authentication)
- AccessKey expired or revoked
- Incorrect permissions for AccessKey or RAM Role
- STS token expired (if using STS authentication)
- OIDC token expired or invalid (if using OIDC authentication)
- Service Account not properly configured with RRSA annotations (for OIDC)
- Missing or incorrect RAM Role ARN in Service Account annotation (for OIDC)

**Solutions:**

- For access_key authentication: Verify AccessKey ID and Secret are correct
- For STS authentication: Verify the security token is valid and not expired
- For OIDC authentication:
  - Verify Service Account has correct RRSA annotations (`pod-identity.alibabacloud.com/role-name`)
  - Check that OIDC provider is properly configured in Alibaba Cloud
  - Verify RAM Role has correct permissions
  - Check OIDC token file exists at `/var/run/secrets/tokens/oidc-token` (default path)
- Verify region configuration is correct
- Check network connectivity
- View diagnostic URL in error message

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

### 5. Webhook Notifications Not Working

**Symptoms:** Webhook is configured but no notifications are received

**Possible Causes:**

- Webhook secret doesn't exist or is missing the required key
- Webhook secret value is empty or invalid
- `WEBHOOK_URL` environment variable is not set in the pod
- Webhook URL is not accessible from the cluster
- Webhook endpoint returns non-2xx status codes
- Event type is not enabled in `WEBHOOK_ENABLED_EVENTS`

**Solutions:**

1. **Verify webhook secret exists and has correct value:**

```bash
# Check if secret exists
kubectl get secret cert-renewer-webhook -n <namespace>

# Check secret keys
kubectl get secret cert-renewer-webhook -n <namespace> -o jsonpath='{.data}' | jq 'keys'

# Decode and view webhook URL (replace <namespace> with your namespace)
kubectl get secret cert-renewer-webhook -n <namespace> -o jsonpath='{.data.webhook-url}' | base64 -d

# Create or update the secret if missing
kubectl create secret generic cert-renewer-webhook \
  --from-literal=webhook-url=https://your-webhook-url-here \
  --namespace=<namespace> \
  --dry-run=client -o yaml | kubectl apply -f -
```

2. **Check pod environment variables:**

```bash
# Get pod name
POD_NAME=$(kubectl get pods -n <namespace> -l app.kubernetes.io/name=cloud-cert-renewer -o jsonpath='{.items[0].metadata.name}')

# Check if WEBHOOK_URL is set in init container
kubectl get pod $POD_NAME -n <namespace> -o jsonpath='{.spec.initContainers[?(@.name=="cert-renewer")].env[?(@.name=="WEBHOOK_URL")]}'

# View init container logs for webhook-related messages
kubectl logs $POD_NAME -n <namespace> -c cert-renewer | grep -i webhook
```

3. **Use diagnostic script:**

```bash
# Run the diagnostic script
NAMESPACE=<your-namespace> SECRET_NAME=cert-renewer-webhook ./scripts/diagnose-webhook.sh
```

4. **Verify webhook URL is accessible:**

```bash
# Test webhook URL from within the cluster (if you have a debug pod)
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl -X POST 'https://your-webhook-url' \
  -H 'Content-Type: application/json' \
  -d '{"test":"message"}'
```

5. **Check webhook configuration in values file:**

Ensure your Helm values file has:

```yaml
webhook:
  enabled: true
  secret:
    name: cert-renewer-webhook # Must match the secret name
    key: webhook-url # Must match the secret key
  timeout: 30
  retryAttempts: 3
  retryDelay: 1.0
  enabledEvents: "all" # Or specific events: "renewal_success,renewal_failed"
```

6. **Verify Helm chart rendered correctly:**

```bash
# Check rendered deployment template
helm template <release-name> ./helm/cloud-cert-renewer -f <values-file> | grep -A 10 WEBHOOK_URL
```

7. **Check application logs for webhook errors:**

```bash
# View logs for webhook-related errors
kubectl logs <pod-name> -n <namespace> -c cert-renewer | grep -i "webhook\|error"
```

**Common Issues:**

- **Secret name mismatch**: Ensure `webhook.secret.name` in values file matches the actual secret name
- **Secret key mismatch**: Ensure `webhook.secret.key` in values file matches the key in the secret
- **Empty secret value**: The webhook URL must be non-empty, otherwise webhook service won't initialize
- **Namespace mismatch**: Ensure secret is in the same namespace as the deployment
- **Webhook URL format**: URL must start with `http://` or `https://`

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

- In production environments, use more secure authentication methods (such as STS or OIDC/RRSA) instead of directly using AccessKey
- For Kubernetes deployments, prefer OIDC (RRSA) authentication over AccessKey for better security
- Do not hardcode sensitive information in code
- Use Kubernetes Secrets to manage sensitive data (when not using OIDC)
- Rotate credentials regularly
- Use least privilege principle for IAM permissions
- When using OIDC authentication, ensure Service Account has proper RRSA annotations configured

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
