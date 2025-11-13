# alibaba-cloud-cert-renewer

A Helm chart for Alibaba Cloud certificate renewal service supporting CDN and SLB.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- cert-manager (for automatic certificate management)
- Reloader (optional, for automatic deployment on certificate updates)

## Installation

### Basic Installation

```bash
helm install alibaba-cloud-cert-renewer ./helm/alibaba-cloud-cert-renewer
```

### Installation with Custom Values

```bash
helm install alibaba-cloud-cert-renewer ./helm/alibaba-cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=example.com \
  --set image.tag=v0.1.0
```

### Installation from Values File

```bash
helm install alibaba-cloud-cert-renewer ./helm/alibaba-cloud-cert-renewer \
  -f my-values.yaml
```

## Configuration

The following table lists the configurable parameters and their default values:

| Parameter                              | Description                           | Default                      |
| -------------------------------------- | ------------------------------------- | ---------------------------- |
| `serviceType`                          | Service type: `cdn` or `slb`          | `cdn`                        |
| `image.repository`                     | Image repository                      | `alibaba-cloud-cert-renewer` |
| `image.tag`                            | Image tag                             | `latest`                     |
| `image.pullPolicy`                     | Image pull policy                     | `IfNotPresent`               |
| `replicas`                             | Number of replicas                    | `1`                          |
| `cdn.domainName`                       | CDN domain name                       | `schema.amugua.com`          |
| `cdn.region`                           | CDN region                            | `cn-hangzhou`                |
| `slb.instanceId`                       | SLB instance ID                       | `""`                         |
| `slb.region`                           | SLB region                            | `cn-hangzhou`                |
| `secrets.alibabaCloudCredentials.name` | Alibaba Cloud credentials secret name | `alibaba-cloud-credentials`  |
| `secrets.certificate.name`             | Certificate secret name               | `cert-secret`                |
| `reloader.enabled`                     | Enable Reloader annotations           | `true`                       |
| `namespace`                            | Kubernetes namespace                  | `default`                    |

## Secrets

### Alibaba Cloud Credentials Secret

Create a secret with your Alibaba Cloud credentials:

```bash
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
cdn:
  domainName: example.com
  region: cn-hangzhou
```

### SLB Certificate Renewal

```yaml
serviceType: slb
slb:
  instanceId: lb-xxxxxxxxx
  region: cn-hangzhou
```

## Upgrading

```bash
helm upgrade alibaba-cloud-cert-renewer ./helm/alibaba-cloud-cert-renewer
```

## Uninstalling

```bash
helm uninstall alibaba-cloud-cert-renewer
```

## How It Works

1. **Init Container**: Runs the certificate renewal script when the pod starts or when the certificate secret changes (via Reloader)
2. **Main Container**: A placeholder container that keeps the deployment running
3. **Reloader**: Monitors the certificate secret and triggers a pod restart when it changes

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=alibaba-cloud-cert-renewer
```

### View Init Container Logs

```bash
kubectl logs <pod-name> -c cert-renewer
```

### View Main Container Logs

```bash
kubectl logs <pod-name> -c placeholder
```

## License

[Add your license here]
