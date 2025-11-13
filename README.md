# 自动更新阿里云HTTPS证书

自动更新阿里云HTTPS证书工具，支持CDN和SLB产品。

## 功能特性

- 支持阿里云CDN证书自动更新
- 支持阿里云SLB证书自动更新
- 证书有效性验证（域名匹配、过期时间检查）
- 支持通配符域名证书
- 支持从环境变量或Kubernetes Secret读取配置
- 完善的错误处理和日志记录

## 环境要求

- Python 3.8+
- uv（Python包管理工具）

## 安装

### 使用 uv 安装依赖

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

## 配置

### 环境变量

项目支持通过环境变量或 `.env` 文件配置。参考 `.env.example` 文件创建 `.env` 文件。

#### 必需的环境变量

- `ALIBABA_CLOUD_ACCESS_KEY_ID`: 阿里云AccessKey ID
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`: 阿里云AccessKey Secret
- `SERVICE_TYPE`: 服务类型，可选值：`cdn` 或 `slb`

#### CDN 配置（当 SERVICE_TYPE=cdn 时）

- `CDN_DOMAIN_NAME`: CDN域名
- `CDN_CERT`: SSL证书内容（PEM格式，支持多行）
- `CDN_CERT_PRIVATE_KEY`: SSL证书私钥（PEM格式，支持多行）
- `CDN_REGION`: 区域（默认：`cn-hangzhou`）

#### SLB 配置（当 SERVICE_TYPE=slb 时）

- `SLB_INSTANCE_ID`: SLB实例ID
- `SLB_CERT`: SSL证书内容（PEM格式，支持多行）
- `SLB_CERT_PRIVATE_KEY`: SSL证书私钥（PEM格式，支持多行）
- `SLB_REGION`: 区域（默认：`cn-hangzhou`）

### 证书格式说明

在 `.env` 文件中，证书和私钥可以使用多行格式，使用三引号包裹：

```env
CDN_CERT="""-----BEGIN CERTIFICATE-----
证书内容...
-----END CERTIFICATE-----"""
```

这样可以确保证书内容不被转义或变形。

## 使用方法

### 本地运行

1. 创建 `.env` 文件（参考 `test_data.env.example`）
2. 配置必要的环境变量
3. 运行程序：

```bash
uv run python main.py
```

### Kubernetes 部署

#### 前置条件

- Kubernetes 集群
- cert-manager（用于自动获取和更新证书）
- Reloader（用于监听证书Secret变化并触发重新部署）

#### 部署步骤

1. **创建阿里云凭证Secret**

```bash
kubectl create secret generic alibaba-cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
```

2. **创建证书Secret**

证书Secret通常由cert-manager自动创建，格式如下：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cert-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64编码的证书>
  tls.key: <base64编码的私钥>
```

3. **构建Docker镜像**

```bash
docker build -t renew-cert-alibaba-cloud:latest .
```

4. **部署应用**

修改 `k8s/deployment.yaml` 中的配置，然后部署：

```bash
kubectl apply -f k8s/deployment.yaml
```

#### Reloader 配置

Deployment 中已配置 Reloader 注解，当 `cert-secret` Secret 发生变化时，会自动触发 Deployment 重新部署，init 容器会执行证书更新。

#### 工作原理

1. cert-manager 自动获取/更新 Let's Encrypt 证书，并更新到 `cert-secret` Secret
2. Reloader 检测到 Secret 变化，触发 Deployment 重新部署
3. init 容器启动，从 Secret 读取证书，调用阿里云API更新证书
4. init 容器执行完成后退出
5. 主容器（占位容器）保持运行，确保 Deployment 状态正常

## 现有环境说明

Let's Encrypt SSL 证书当前使用 Kubernetes 部署的 `cert-manager` 来自动获取和自动更新。

已部署"[stakater/Reloader](https://github.com/stakater/Reloader)"应用。在 Deployment 当中加入特定注解，即可跟踪某一 ConfigMap/Secret 的变化。当 ConfigMap/Secret 发生变化时，可自动重新部署（如 Rollout Restart）该 Deployment。

## 设计思路

建立一个 Deployment，其中有两个容器，一个是 init 容器，另一个是名义上的主容器。

1. **主容器**：主容器为一个占位应用（busybox），只是用来占位，实际上不会被使用。
2. **init 容器**：init 容器用来响应前述的 Reloader，用以获取证书的 secret，并调用阿里云的 API，更新相应产品项（SLB实例或CDN实例）的证书。

将证书更新的动作放在 init 容器中，是因为主容器的生命周期是长期的，而 init 容器是一次性的，运行完成后可以退出。而主容器需要一直运行，以保证 Deployment 不会处于失败状态。

每个 SLB 实例或 CDN 实例，都需要一个对应的 Deployment，用以更新证书。

## 开发

### 运行测试

```bash
uv run pytest
```

### 代码结构

```
renew-cert-alibaba-cloud/
├── main.py                    # 主程序入口
├── dianplus/                  # 核心功能模块
│   └── utils/
│       └── ssl_cert_parser.py # SSL证书解析和验证工具
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── test_main.py           # 主程序测试
│   └── test_ssl_cert_parser.py # SSL证书解析器测试
├── k8s/                       # Kubernetes部署配置
│   └── deployment.yaml        # Deployment配置
├── Dockerfile                 # Docker镜像构建文件
├── .env.example               # 环境变量配置示例
├── pyproject.toml             # 项目配置和依赖（使用uv）
└── README.md                  # 项目说明
```

## 注意事项

1. **安全性**：生产环境中，请使用更安全的认证方式（如STS），而不是直接使用AccessKey
2. **证书格式**：确保证书和私钥格式正确，使用PEM格式
3. **区域配置**：根据实际使用的阿里云区域配置正确的区域代码
4. **错误处理**：程序会记录详细的日志，便于排查问题

## 许可证

[根据项目实际情况添加许可证信息]
