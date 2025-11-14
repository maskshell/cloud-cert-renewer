# 自动更新云服务HTTPS证书

自动更新云服务HTTPS证书工具，支持CDN和负载均衡器产品。当前主要支持阿里云，架构设计支持多云扩展。

## 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装](#安装)
- [配置](#配置)
- [使用方法](#使用方法)
- [Kubernetes 部署](#kubernetes-部署)
- [开发](#开发)
- [故障排查](#故障排查)
- [注意事项](#注意事项)

## 功能特性

- 支持云服务CDN证书自动更新（当前支持阿里云）
- 支持云服务负载均衡器证书自动更新（当前支持阿里云SLB）
- 证书有效性验证（域名匹配、过期时间检查）
- 支持通配符域名证书
- 支持从环境变量或Kubernetes Secret读取配置
- 完善的错误处理和日志记录
- 支持 Helm Chart 部署
- 与 cert-manager 和 Reloader 集成

## 快速开始

### 本地快速测试

```bash
# 1. 克隆项目
git clone <repository-url>
cd cloud-cert-renewer

# 2. 安装依赖
uv sync --extra dev

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 4. 运行程序
uv run python main.py
```

### Kubernetes 快速部署

```bash
# 1. 创建 Secret（使用通用命名，推荐）
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_KEY \
  --from-literal=access-key-secret=YOUR_SECRET

# 或使用旧命名（向后兼容）
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_KEY \
#   --from-literal=access-key-secret=YOUR_SECRET

# 2. 使用 Helm 部署
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=your-domain.com
```

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

- `CLOUD_ACCESS_KEY_ID`: 云服务AccessKey ID（新名称，优先使用）
- `CLOUD_ACCESS_KEY_SECRET`: 云服务AccessKey Secret（新名称，优先使用）
- `ALIBABA_CLOUD_ACCESS_KEY_ID`: 阿里云AccessKey ID（旧名称，向后兼容）
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`: 阿里云AccessKey Secret（旧名称，向后兼容）
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

1. 创建 `.env` 文件（参考 `.env.example`）

   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，配置必要的环境变量

3. 运行程序：

   ```bash
   uv run python main.py
   ```

### 测试运行

运行所有测试：

```bash
# 安装开发依赖（如果还没有安装）
uv sync --extra dev

# 运行所有测试
uv run pytest

# 运行测试（详细输出）
uv run pytest -v

# 运行特定测试文件
uv run pytest tests/test_main.py

# 运行特定测试类
uv run pytest tests/test_main.py::TestCdnCertsRenewer

# 显示覆盖率
uv run pytest --cov=. --cov-report=html
```

### Kubernetes 部署

#### 前置条件

- Kubernetes 集群
- cert-manager（用于自动获取和更新证书）
- Reloader（用于监听证书Secret变化并触发重新部署）

#### 部署方式

##### 方式一：使用 Helm Chart（推荐）

1. **创建云服务凭证Secret（使用通用命名，推荐）**

```bash
# 使用通用命名（推荐）
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET

# 或使用旧命名（向后兼容）
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
#   --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
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
docker build -t cloud-cert-renewer:latest .
```

4. **使用 Helm 部署**

```bash
# 使用默认配置部署（CDN）
helm install cloud-cert-renewer ./helm/cloud-cert-renewer

# 使用自定义配置部署
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set serviceType=cdn \
  --set cdn.domainName=example.com \
  --set image.tag=latest

# 使用示例 values 文件部署
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-cdn.yaml
```

##### 方式二：使用原生 Kubernetes YAML

1. **创建云服务凭证Secret（使用通用命名，推荐）**

```bash
# 使用通用命名（推荐）
kubectl create secret generic cloud-credentials \
  --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET

# 或使用旧命名（向后兼容）
# kubectl create secret generic alibaba-cloud-credentials \
#   --from-literal=access-key-id=YOUR_ACCESS_KEY_ID \
#   --from-literal=access-key-secret=YOUR_ACCESS_KEY_SECRET
```

2. **创建证书Secret**

证书Secret通常由cert-manager自动创建。

3. **构建Docker镜像**

```bash
docker build -t cloud-cert-renewer:latest .
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
3. init 容器启动，从 Secret 读取证书，调用云服务API更新证书
4. init 容器执行完成后退出
5. 主容器（占位容器）保持运行，确保 Deployment 状态正常

#### Helm Chart 详细使用

**查看所有可配置参数：**

```bash
helm show values ./helm/cloud-cert-renewer
```

**使用示例 values 文件：**

```bash
# CDN 证书更新
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-cdn.yaml

# SLB 证书更新
helm install cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-slb.yaml
```

**升级部署：**

```bash
# 升级到新版本
helm upgrade cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set image.tag=v0.2.0

# 升级并修改配置
helm upgrade cloud-cert-renewer ./helm/cloud-cert-renewer \
  --set cdn.domainName=new-domain.com
```

**验证模板渲染：**

```bash
# 查看渲染后的 YAML（不实际部署）
helm template cloud-cert-renewer ./helm/cloud-cert-renewer

# 使用自定义 values 查看
helm template cloud-cert-renewer ./helm/cloud-cert-renewer \
  -f ./helm/cloud-cert-renewer/values-cdn.yaml
```

**检查 Chart：**

```bash
helm lint ./helm/cloud-cert-renewer
```

## 现有环境说明

Let's Encrypt SSL 证书当前使用 Kubernetes 部署的 `cert-manager` 来自动获取和自动更新。

已部署"[stakater/Reloader](https://github.com/stakater/Reloader)"应用。在 Deployment 当中加入特定注解，即可跟踪某一 ConfigMap/Secret 的变化。当 ConfigMap/Secret 发生变化时，可自动重新部署（如 Rollout Restart）该 Deployment。

## 设计思路

建立一个 Deployment，其中有两个容器，一个是 init 容器，另一个是名义上的主容器。

1. **主容器**：主容器为一个占位应用（busybox），只是用来占位，实际上不会被使用。
2. **init 容器**：init 容器用来响应前述的 Reloader，用以获取证书的 secret，并调用云服务的 API，更新相应产品项（负载均衡器实例或CDN实例）的证书。

将证书更新的动作放在 init 容器中，是因为主容器的生命周期是长期的，而 init 容器是一次性的，运行完成后可以退出。而主容器需要一直运行，以保证 Deployment 不会处于失败状态。

每个 SLB 实例或 CDN 实例，都需要一个对应的 Deployment，用以更新证书。

## 开发

### 环境设置

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖和开发依赖
uv sync --extra dev
```

### 代码格式化

```bash
# 使用 ruff 格式化代码
uv run ruff format .

# 使用 black 格式化代码
uv run black .

# 检查代码格式（不修改）
uv run black . --check
```

### 代码检查

```bash
# 使用 ruff 进行 lint 检查
uv run ruff check .

# 使用 ruff 自动修复问题
uv run ruff check . --fix
```

### YAML 文件格式化

项目已配置 `yamllint` 和 `pre-commit` 用于 YAML 文件检查和格式化。

**使用 yamllint 检查 YAML 文件：**

```bash
# 检查所有 YAML 文件
uv run yamllint .

# 检查特定文件
uv run yamllint k8s/deployment.yaml

# 检查并自动修复（部分问题）
uv run yamllint --format parsable k8s/deployment.yaml
```

**使用 pre-commit（推荐）：**

```bash
# 安装 pre-commit 钩子（在 git commit 时自动运行）
uv run pre-commit install

# 手动运行所有检查
uv run pre-commit run --all-files

# 只检查 YAML 文件
uv run pre-commit run yamllint --all-files
```

**推荐的 YAML 格式化工具：**

1. **yamllint**（已安装）- YAML 语法检查和风格检查
   - 优点：轻量、快速、可配置
   - 缺点：不直接格式化，只检查和报告问题

2. **pre-commit**（已安装）- Git 钩子管理工具
   - 优点：集成多种工具，自动化检查
   - 缺点：需要 Git 仓库

3. **yamlfmt**（可选）- 专门的 YAML 格式化工具

   ```bash
   # 使用 Go 安装
   go install github.com/google/yamlfmt/cmd/yamlfmt@latest
   ```

4. **prettier**（可选）- 通用代码格式化工具

   ```bash
   # 使用 npm 安装
   npm install -g prettier
   prettier --write "**/*.yaml" "**/*.yml"
   ```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行测试（详细输出）
uv run pytest -v

# 运行测试（显示打印输出）
uv run pytest -s

# 运行特定测试文件
uv run pytest tests/test_main.py

# 运行特定测试类
uv run pytest tests/test_main.py::TestCdnCertsRenewer

# 运行特定测试方法
uv run pytest tests/test_main.py::TestCdnCertsRenewer::test_create_client

# 在第一个失败时停止
uv run pytest -x

# 显示最慢的 10 个测试
uv run pytest --durations=10

# 生成覆盖率报告
uv run pytest --cov=. --cov-report=html
```

### 构建 Docker 镜像

```bash
# 构建镜像
docker build -t cloud-cert-renewer:latest .

# 构建并指定标签
docker build -t cloud-cert-renewer:v0.1.0 .

# 测试运行镜像
docker run --rm \
  -e ALIBABA_CLOUD_ACCESS_KEY_ID=your_key \
  -e ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_secret \
  -e SERVICE_TYPE=cdn \
  -e CDN_DOMAIN_NAME=example.com \
  -e CDN_CERT="$(cat cert.pem)" \
  -e CDN_CERT_PRIVATE_KEY="$(cat key.pem)" \
  cloud-cert-renewer:latest
```

### 代码结构

```
cloud-cert-renewer/
├── main.py                    # 主程序入口
├── cloud_cert_renewer/        # 核心功能模块
│   ├── auth/                  # 鉴权模块（支持多种鉴权方式）
│   │   ├── base.py            # 鉴权提供者抽象接口
│   │   ├── access_key.py      # AK/SK鉴权提供者
│   │   ├── sts.py             # STS临时凭证鉴权提供者
│   │   ├── iam_role.py        # IAM Role鉴权提供者
│   │   ├── service_account.py # ServiceAccount鉴权提供者
│   │   ├── env.py             # 环境变量鉴权提供者
│   │   └── factory.py         # 鉴权提供者工厂
│   ├── cert_renewer/          # 证书更新器模块（策略模式）
│   │   ├── base.py            # 抽象基类（模板方法模式）
│   │   ├── cdn_renewer.py     # CDN证书更新策略
│   │   ├── load_balancer_renewer.py # 负载均衡器证书更新策略
│   │   └── factory.py         # 证书更新器工厂
│   ├── clients/               # 客户端模块
│   │   └── alibaba.py        # 阿里云客户端封装
│   ├── config/                # 配置模块
│   │   ├── models.py          # 配置数据类
│   │   └── loader.py          # 配置加载器
│   ├── providers/             # 云服务提供商适配器（适配器模式）
│   │   ├── base.py            # 云服务适配器接口
│   │   ├── alibaba.py         # 阿里云适配器
│   │   ├── aws.py             # AWS适配器（预留）
│   │   └── azure.py           # Azure适配器（预留）
│   ├── utils/                 # 工具模块
│   │   └── ssl_cert_parser.py # SSL证书解析和验证工具
│   ├── container.py           # 依赖注入容器
│   ├── config.py              # 向后兼容导入
│   ├── renewer.py             # 向后兼容导入
│   └── adapters.py            # 向后兼容导入
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── test_main.py           # 主程序测试
│   └── test_ssl_cert_parser.py # SSL证书解析器测试
├── k8s/                       # Kubernetes原生部署配置
│   └── deployment.yaml        # Deployment配置
├── helm/                      # Helm Chart
│   └── cloud-cert-renewer/
│       ├── Chart.yaml         # Chart元数据
│       ├── values.yaml        # 默认配置值
│       ├── values-cdn.yaml    # CDN示例配置
│       ├── values-slb.yaml    # SLB示例配置
│       └── templates/         # Kubernetes资源模板
│           ├── _helpers.tpl   # 辅助模板
│           └── deployment.yaml
├── Dockerfile                 # Docker镜像构建文件
├── .env.example               # 环境变量配置示例
├── pyproject.toml             # 项目配置和依赖（使用uv）
└── README.md                  # 项目说明
```

## 故障排查

### 常见问题

#### 1. 证书验证失败

**症状：** 日志显示 "证书验证失败：域名 xxx 不在证书中或证书已过期"

**解决方案：**

- 检查证书是否包含目标域名
- 检查证书是否已过期
- 确认证书格式正确（PEM格式）
- 对于通配符证书，确认域名匹配规则

#### 2. 配置错误

**症状：** 日志显示 "配置错误：缺少必要的环境变量"

**解决方案：**

- 检查所有必需的环境变量是否已设置
- 确认环境变量名称拼写正确
- 检查 Secret 是否存在且包含正确的 key

#### 3. API 调用失败

**症状：** 日志显示 "CDN证书更新失败" 或 "SLB证书更新失败"

**解决方案：**

- 检查 AccessKey 是否正确且有相应权限
- 确认区域配置正确
- 检查网络连接
- 查看错误消息中的诊断地址

#### 4. Kubernetes 部署问题

**检查 Pod 状态：**

```bash
# 查看 Pod 列表
kubectl get pods -l app.kubernetes.io/name=cloud-cert-renewer

# 查看 Pod 详细信息
kubectl describe pod <pod-name>

# 查看 init 容器日志
kubectl logs <pod-name> -c cert-renewer

# 查看主容器日志
kubectl logs <pod-name> -c placeholder

# 查看 Pod 事件
kubectl get events --field-selector involvedObject.name=<pod-name>
```

**检查 Secret：**

```bash
# 查看 Secret 是否存在
kubectl get secret alibaba-cloud-credentials
kubectl get secret cert-secret

# 查看 Secret 内容（base64 解码）
kubectl get secret cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d
```

**检查 Reloader：**

```bash
# 查看 Reloader 是否运行
kubectl get pods -n <reloader-namespace> -l app=reloader

# 查看 Reloader 日志
kubectl logs -n <reloader-namespace> <reloader-pod-name>
```

### 调试技巧

1. **本地测试配置：**

   ```bash
   # 从 Kubernetes Secret 导出环境变量进行本地测试
   kubectl get secret cert-secret -o jsonpath='{.data.tls\.crt}' | base64 -d > cert.pem
   kubectl get secret cert-secret -o jsonpath='{.data.tls\.key}' | base64 -d > key.pem
   ```

2. **启用详细日志：**
   程序使用 Python logging，日志级别可通过环境变量控制（如果实现）

3. **验证证书内容：**

   ```bash
   # 查看证书信息
   openssl x509 -in cert.pem -text -noout

   # 检查证书过期时间
   openssl x509 -in cert.pem -noout -dates
   ```

## 注意事项

1. **安全性**：
   - 生产环境中，请使用更安全的认证方式（如STS），而不是直接使用AccessKey
   - 不要在代码中硬编码敏感信息
   - 使用 Kubernetes Secret 管理敏感数据

2. **证书格式**：
   - 确保证书和私钥格式正确，使用PEM格式
   - 证书链应包含完整的证书链（服务器证书 + 中间证书 + 根证书）
   - 私钥格式应为 RSA 或 ECDSA

3. **区域配置**：
   - 根据实际使用的云服务区域配置正确的区域代码
   - 常见区域：`cn-hangzhou`、`cn-beijing`、`cn-shanghai`、`cn-shenzhen` 等

4. **错误处理**：
   - 程序会记录详细的日志，便于排查问题
   - 建议配置日志收集系统（如 ELK、Loki）进行集中管理

5. **资源限制**：
   - 根据实际负载调整资源请求和限制
   - init 容器执行时间通常很短，但需要足够的资源完成 API 调用

6. **多实例部署**：
   - 每个 CDN 域名或 SLB 实例需要单独的 Deployment
   - 使用不同的 release name 或 namespace 进行区分

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 使用 `black` 格式化代码
- 使用 `ruff` 进行代码检查
- 编写单元测试
- 更新相关文档

## 许可证

[根据项目实际情况添加许可证信息]
