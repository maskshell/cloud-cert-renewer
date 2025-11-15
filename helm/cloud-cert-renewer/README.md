# cloud-cert-renewer

A Helm chart for cloud certificate renewal service supporting CDN and Load Balancer. Supports multiple cloud providers (currently Alibaba Cloud, with architecture designed for multi-cloud extension).

## Prerequisites

**Required:**

- Kubernetes 1.19+
- Helm 3.0+

**Recommended:**

- cert-manager (for automatic certificate management)
- Reloader (for automatic deployment on certificate updates)

## Installation

### Basic Installation

```bash
helm install cloud-cert-renewer ./helm/cloud-cert-renewer
```

### Installation with Custom Values

```bash
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=example.com \
  --set image.tag=v0.1.0
```

### Installation from Values File

```bash
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f my-values.yaml
```

## Configuration

The following table lists the configurable parameters and their default values:

| Parameter                              | Description                           | Default                      |
| -------------------------------------- | ------------------------------------- | ---------------------------- |
| `serviceType`                          | Service type: `cdn` or `lb` (backward compatible: `slb`) | `cdn`                        |
| `cloudProvider`                         | Cloud provider: `alibaba`, `aws`, `azure`, etc. (currently supports Alibaba Cloud) | `alibaba`                    |
| `authMethod`                           | Authentication method: `access_key`, `sts`, `iam_role`, `service_account`, `env` | `access_key`                 |
| `image.repository`                     | Image repository                      | `cloud-cert-renewer`         |
| `image.tag`                            | Image tag                             | `latest`                     |
| `image.pullPolicy`                     | Image pull policy                     | `IfNotPresent`               |
| `replicas`                             | Number of replicas                    | `1`                          |
| `cdn.domainName`                       | CDN domain name                       | `schema.amugua.com`          |
| `cdn.region`                           | CDN region                            | `cn-hangzhou`                |
| `lb.instanceId`                        | Load Balancer instance ID (new name, preferred) | `""`                         |
| `lb.listenerPort`                      | Load Balancer listener port           | `443`                        |
| `lb.region`                            | Load Balancer region                  | `cn-hangzhou`                |
| `slb.instanceId`                       | SLB instance ID (old name, backward compatible)    | `""`                         |
| `slb.region`                           | SLB region (old name, backward compatible)         | `cn-hangzhou`                |
| `secrets.cloudCredentials.name`        | Cloud service credentials secret name (new name, preferred) | `cloud-credentials`           |
| `secrets.cloudCredentials.accessKeyIdKey` | Access key ID key name in credentials secret | `access-key-id`              |
| `secrets.cloudCredentials.accessKeySecretKey` | Access key secret key name in credentials secret | `access-key-secret`          |
| `secrets.cloudCredentials.securityTokenKey` | Security token key in credentials secret (optional, for STS) | `""`                         |
| `secrets.alibabaCloudCredentials.name` | Alibaba Cloud credentials secret name (old name, backward compatible) | `alibaba-cloud-credentials`  |
| `secrets.alibabaCloudCredentials.accessKeyIdKey` | Access key ID key name (old name, backward compatible) | `access-key-id`              |
| `secrets.alibabaCloudCredentials.accessKeySecretKey` | Access key secret key name (old name, backward compatible) | `access-key-secret`          |
| `secrets.certificate.name`             | Certificate secret name               | `cert-secret`                |
| `secrets.certificate.certKey`          | Certificate key name in secret         | `tls.crt`                    |
| `secrets.certificate.privateKeyKey`   | Private key key name in secret         | `tls.key`                    |
| `forceUpdate`                          | Force update certificate even if same | `false`                      |
| `reloader.enabled`                     | Enable Reloader annotations           | `true`                       |
| `reloader.auto`                        | Enable automatic reload (Reloader)     | `true`                       |
| `reloader.search`                      | Enable search mode (Reloader)          | `true`                       |
| `initContainer.resources`              | Init container resource requests/limits | See [Resources](#resources)  |
| `mainContainer.image`                  | Main container image (placeholder)     | `busybox:latest`             |
| `mainContainer.resources`              | Main container resource requests/limits | See [Resources](#resources) |
| `labels`                               | Additional labels for Deployment       | `{}`                         |
| `annotations`                          | Additional annotations for Deployment  | `{}`                         |
| `podAnnotations`                       | Additional annotations for Pods       | `{}`                         |
| `nodeSelector`                         | Node selector for pod scheduling        | `{}`                         |
| `tolerations`                          | Tolerations for pod scheduling          | `[]`                         |
| `affinity`                             | Affinity rules for pod scheduling       | `{}`                         |
| `namespace`                            | Kubernetes namespace                  | `default`                    |

**Note:** The Docker images are built with multi-architecture support (amd64 and arm64). Kubernetes will automatically select the correct architecture based on your node platform.

## Secrets

### Cloud Service Credentials Secret

Create a secret with your cloud service credentials (example: Alibaba Cloud):

```bash
# Use generic naming (recommended)
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET

# Or use old naming (backward compatible)
kubectl create secret generic alibaba-cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
```

### STS Authentication

To use STS (Security Token Service) temporary credentials:

1. Set `authMethod: sts` in your values file
2. Include `security-token` in your credentials secret:

   ```bash
   kubectl create secret generic cloud-credentials \
     --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
     --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET \
     --from-literal=security-token=YOUR_SECURITY_TOKEN
   ```

3. Configure `secrets.cloudCredentials.securityTokenKey: "security-token"` in values

### Force Update

To force certificate update even if it's the same:

```yaml
forceUpdate: true
```

This sets the `FORCE_UPDATE` environment variable to `"true"`.

### Resources

You can configure resource requests and limits for both the init container and main container:

```yaml
initContainer:
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi

mainContainer:
  image: busybox:latest
  resources:
    requests:
      cpu: 10m
      memory: 32Mi
    limits:
      cpu: 100m
      memory: 128Mi
```

### Certificate Secret

The certificate secret is typically created by cert-manager. It should contain:

- `tls.crt`: The SSL certificate (PEM format)
- `tls.key`: The private key (PEM format)

## RAM Permissions (Alibaba Cloud)

When using Alibaba Cloud, you need to configure appropriate RAM (Resource Access Management) permissions for the AccessKey. The following permissions are recommended:

### Recommended Custom Policy

For CDN certificate renewal:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cdn:SetCdnDomainSSLCertificate",
        "cdn:DescribeDomainCertificateInfo"
      ],
      "Resource": "*"
    }
  ]
}
```

For Load Balancer (SLB) certificate renewal:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "slb:DescribeServerCertificates",
        "slb:UploadServerCertificate"
      ],
      "Resource": "*"
    }
  ]
}
```

For both CDN and Load Balancer:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cdn:SetCdnDomainSSLCertificate",
        "cdn:DescribeDomainCertificateInfo"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "slb:DescribeServerCertificates",
        "slb:UploadServerCertificate"
      ],
      "Resource": "*"
    }
  ]
}
```

### System Policy Alternative

Alternatively, you can use the system policy `AliyunSLBReadOnlyAccess` combined with the following custom policy:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Action": [
        "slb:Describe*",
        "slb:List*",
        "slb:Get*"
      ],
      "Resource": "*",
      "Effect": "Allow"
    },
    {
      "Action": "cms:QueryMetric*",
      "Resource": "*",
      "Effect": "Allow"
    }
  ]
}
```

**Note:** The system policy `AliyunSLBReadOnlyAccess` provides read-only access. You still need to add write permissions for `slb:UploadServerCertificate` and `cdn:SetCdnDomainSSLCertificate` through a custom policy.

### Security Best Practices

- Use the principle of least privilege: only grant the minimum permissions required
- Use STS (Security Token Service) temporary credentials when possible instead of permanent AccessKeys
- Regularly rotate AccessKeys
- Use different AccessKeys for different environments (development, staging, production)

## Examples

### CDN Certificate Renewal

```yaml
serviceType: cdn
cloudProvider: alibaba
cdn:
  domainName: example.com
  region: cn-hangzhou
```

### Load Balancer Certificate Renewal

```yaml
serviceType: lb  # or use slb (backward compatible)
cloudProvider: alibaba
lb:
  instanceId: lb-xxxxxxxxx
  listenerPort: 443
  region: cn-hangzhou
```

## Upgrading

```bash
helm upgrade cloud-cert-renewer ./helm/cloud-cert-renewer
```

## Uninstalling

```bash
helm uninstall cloud-cert-renewer
```

## How It Works

1. **Init Container**: Runs the certificate renewal script when the pod starts or when the certificate secret changes (via Reloader)
2. **Main Container**: A placeholder container that keeps the deployment running
3. **Reloader**: Monitors the certificate secret and triggers a pod restart when it changes

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=cloud-cert-renewer
```

### View Init Container Logs

```bash
kubectl logs <pod-name> -c cert-renewer
```

### View Main Container Logs

```bash
kubectl logs <pod-name> -c placeholder
```

## Advanced Configuration

### Custom Labels and Annotations

You can add custom labels and annotations to the Deployment and Pods:

```yaml
labels:
  environment: production
  team: platform

annotations:
  deployment.kubernetes.io/revision: "1"

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
```

### Node Selector and Affinity

Configure pod scheduling using node selectors, tolerations, and affinity rules:

```yaml
nodeSelector:
  kubernetes.io/os: linux
  node-type: compute

tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "cert-renewer"
    effect: "NoSchedule"

affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/os
          operator: In
          values:
          - linux
```

## Multi-Cloud Support

This chart is designed to support multiple cloud providers. Currently, Alibaba Cloud is fully supported. The architecture allows for easy extension to other cloud providers (AWS, Azure, etc.) by implementing the corresponding adapters.

To use a different cloud provider, set the `cloudProvider` value accordingly (when support is added):

```yaml
cloudProvider: aws  # or azure, etc.
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
