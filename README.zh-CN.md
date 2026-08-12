# Cloud Certificate Renewer

[English](README.md) | **简体中文**

面向云服务的 HTTPS 证书自动续期工具，支持 CDN 与负载均衡（Load Balancer）产品。它通常以 Kubernetes init-container 形式与 cert-manager、Reloader 配合运行，也可作为独立的 CLI 使用。当前支持阿里云，架构上预留了多云扩展能力。

## 目录

- [特性](#特性)
- [Kubernetes 部署](#kubernetes-部署)
- [CLI 安装](#cli-安装)
- [SLB CAS 证书中转路径](#slb-cas-证书中转路径)
- [文档](#文档)
- [贡献](#贡献)
- [许可证](#许可证)

## 特性

- 自动续期云 CDN 服务的证书（当前支持阿里云）
- 自动续期云负载均衡服务的证书，支持多实例且每个实例可配置独立端口（当前支持阿里云 SLB）
- 可选的 CAS 中转上传路径（`LB_CERT_SOURCE=cas`），供 WAF 等服务引用 SLB 证书
- 证书校验（域名匹配、过期检查）
- 支持泛域名证书
- CLI 支持，提供 `--dry-run`、`--verbose`、`--version` 等参数
- 多种认证方式：
  - Access Key 认证
  - STS（安全令牌服务）临时凭证
  - IAM Role 认证
  - 面向 Kubernetes 的 OIDC（RRSA）认证
  - Service Account 认证
  - 环境变量认证
- 通过环境变量或 Kubernetes Secret 进行配置
- 完善的错误处理与日志
- 支持 Helm Chart 部署
- 与 cert-manager、Reloader 集成

## Kubernetes 部署

### 前置条件

**必需：**

- Kubernetes 集群

**推荐：**

- cert-manager（用于自动申请与续期证书）
- Reloader（用于监听证书 Secret 变化并自动触发 Deployment 重新部署）

### 部署

```bash
# 1. 创建 Secret（推荐使用通用命名）
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_KEY \
  --from-literal=access-key-secret=YOUR_SECRET

# 或使用旧版命名（向后兼容）
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_KEY \
#   --from-literal=access-key-secret=YOUR_SECRET

# 2. 使用 Helm 部署
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=your-domain.com
```

更详细的部署说明与排障，请参阅：

- [Helm Chart README](helm/cloud-cert-renewer/README.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 工作原理（集群内续期）

1. cert-manager 自动申请/更新 Let's Encrypt 证书，并更新 `cert-secret` Secret
2. Reloader 检测到 Secret 变化，触发 Deployment 重新部署
3. init-container 启动，从 Secret 读取证书，并调用云服务 API 更新证书
4. 完成后 init-container 退出
5. 主容器（占位容器）持续运行，以保证 Deployment 状态正常

## CLI 安装

### 使用 pip（PyPI）

可直接从 PyPI 安装：

```bash
pip install cloud-cert-renewer
```

安装后，可使用 `cloud-cert-renewer` 命令运行：

```bash
# 查看帮助
cloud-cert-renewer --help

# 以 dry-run 模式运行
cloud-cert-renewer --dry-run --verbose

# 通过环境变量运行
export SERVICE_TYPE=cdn
export CLOUD_ACCESS_KEY_ID=your_key
...
cloud-cert-renewer
```

## SLB CAS 证书中转路径

默认情况下，SLB 证书续期会直接将证书上传到 SLB 证书中心（`LB_CERT_SOURCE=slb`）。当 WAF 等服务要求 SLB 证书引用由 CAS 管理的证书时，可将 `LB_CERT_SOURCE` 设为 `cas`（环境变量名 `LB_CERT_SOURCE`，向后兼容 `SLB_CERT_SOURCE`）。

### 工作原理（cas 路径）

1. 按稳定的证书名称查找已有的 CAS 证书（`ListUserCertificateOrder`，`OrderType=UPLOAD`）。查找过程会分页枚举已上传证书并在客户端按名称精确匹配——因为 API 的 `Keyword` 只匹配域名或资源 ID，不匹配证书名称——找到即复用。
2. 若未找到，则通过 `UploadUserCertificate` 将证书上传到阿里云数字证书管理服务（CAS）。若在此期间有并发上传产生了同名证书（触发 duplicate-name 错误），会捕获该冲突并复用已存在的证书。
3. 通过 `UploadServerCertificate` 将 CAS 证书导入 SLB，传入 `AliCloudCertificateId` 与 `AliCloudCertificateRegionId=cn-hangzhou`（CAS 中国站地域；与 `LB_REGION` 无关）。若已存在指纹匹配的 SLB 服务器证书则复用（幂等）；否则新建一条。
4. 将证书绑定到 HTTPS 监听。

CDN 以及默认的 slb 路径不受影响。

### 证书累积（运维提示）

证书续期**不会**删除旧证书，请注意累积行为：

- **CAS 证书：** cas 路径使用由 SLB 实例 ID 与证书 SHA-1 指纹派生的稳定名称上传（`{instance_id}-{fingerprint[:8]}`）。当证书**内容变化**（例如真实续期）时，指纹变化，会以新名称产生一条**新的** CAS 证书。原 CAS 证书会保留，不会被删除。
- **SLB 服务器证书：** 在 cas 路径上，若 `DescribeServerCertificates` 第一页中可见到指纹匹配的已有 SLB 服务器证书，则复用；否则会**新建**一条 SLB 服务器证书。多次续期后可能留下孤立的 CAS 与 SLB 证书条目。

两条路径均不会自动清理。建议在阿里云控制台定期清理（或配置生命周期策略），退役陈旧的 CAS 证书与不再使用的 SLB 服务器证书。

### 所需 CAS 权限

使用 `LB_CERT_SOURCE=cas` 时，需要为 AccessKey 或 RAM Role 额外授予以下 RAM 权限：

- `yundun-cert:UploadUserCertificate` —— 向 CAS 上传证书
- `yundun-cert:ListUserCertificateOrder` —— 按名称查找已上传的证书（用于幂等）

以上两项均包含在系统策略 `AliyunYundunCertFullAccess` 中。

对于 RRSA/OIDC 场景（Kubernetes），请将 CAS 权限追加到该 Service Account 所使用的 RAM Role 上。

## 文档

- **[CONTRIBUTING.md](CONTRIBUTING.md)**：贡献指南
- **[DEVELOPMENT.md](DEVELOPMENT.md)**：详细开发指南（代码格式化、Lint、测试、构建）
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**：常见问题与排障技巧
- **[Helm Chart README](helm/cloud-cert-renewer/README.md)**：详细的 Kubernetes 部署指南
- **[testing-design-principles.mdc](testing-design-principles.mdc)**：测试设计与实现原则

## 贡献

欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)，其中包含语言规范等指南。

## 许可证

本项目基于 MIT 许可证发布，详见 [LICENSE](LICENSE) 文件。
