# cloud-cert-renewer

A Helm chart for cloud certificate renewal service supporting CDN and Load Balancer. Supports multiple cloud providers (currently Alibaba Cloud, with architecture designed for multi-cloud extension).

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- cert-manager (for automatic certificate management)
- Reloader (optional, for automatic deployment on certificate updates)

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
| `serviceType`                          | Service type: `cdn` or `lb` (向后兼容：`slb`) | `cdn`                        |
| `cloudProvider`                         | Cloud provider: `alibaba`, `aws`, `azure`, etc. (currently supports Alibaba Cloud) | `alibaba`                    |
| `authMethod`                           | Authentication method: `access_key`, `sts`, `iam_role`, `service_account`, `env` | `access_key`                 |
| `image.repository`                     | Image repository                      | `cloud-cert-renewer`         |
| `image.tag`                            | Image tag                             | `latest`                     |
| `image.pullPolicy`                     | Image pull policy                     | `IfNotPresent`               |
| `replicas`                             | Number of replicas                    | `1`                          |
| `cdn.domainName`                       | CDN domain name                       | `schema.amugua.com`          |
| `cdn.region`                           | CDN region                            | `cn-hangzhou`                |
| `lb.instanceId`                        | Load Balancer instance ID (新名称，优先使用) | `""`                         |
| `lb.listenerPort`                      | Load Balancer listener port           | `443`                        |
| `lb.region`                            | Load Balancer region                  | `cn-hangzhou`                |
| `slb.instanceId`                       | SLB instance ID (旧名称，向后兼容)    | `""`                         |
| `slb.region`                           | SLB region (旧名称，向后兼容)         | `cn-hangzhou`                |
| `secrets.cloudCredentials.name`        | Cloud service credentials secret name (新名称，优先使用) | `cloud-credentials`           |
| `secrets.alibabaCloudCredentials.name` | Alibaba Cloud credentials secret name (旧名称，向后兼容) | `alibaba-cloud-credentials`  |
| `secrets.certificate.name`             | Certificate secret name               | `cert-secret`                |
| `reloader.enabled`                     | Enable Reloader annotations           | `true`                       |
| `namespace`                            | Kubernetes namespace                  | `default`                    |

## Secrets

### Cloud Service Credentials Secret

Create a secret with your cloud service credentials (example: Alibaba Cloud):

```bash
# 使用通用命名（推荐）
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET

# 或使用旧命名（向后兼容）
kubectl create secret generic alibaba-cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
```

### Certificate Secret

The certificate secret is typically created by cert-manager. It should contain:

- `tls.crt`: The SSL certificate (PEM format)
- `tls.key`: The private key (PEM format)

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
serviceType: lb  # 或使用 slb（向后兼容）
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

## Multi-Cloud Support

This chart is designed to support multiple cloud providers. Currently, Alibaba Cloud is fully supported. The architecture allows for easy extension to other cloud providers (AWS, Azure, etc.) by implementing the corresponding adapters.

To use a different cloud provider, set the `cloudProvider` value accordingly (when support is added):

```yaml
cloudProvider: aws  # or azure, etc.
```

## License

[Add your license here]
