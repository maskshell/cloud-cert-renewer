# 项目结构说明

## 目录结构

```
alibaba-cloud-cert-renewer/
├── .env                    # 环境变量文件（本地配置，不提交）
├── .env.example            # 环境变量示例文件
├── .gitignore              # Git 忽略文件配置
├── .pre-commit-config.yaml # pre-commit 钩子配置
├── .yamllint               # YAML 文件检查配置
├── Dockerfile              # Docker 镜像构建文件
├── main.py                 # 主程序入口
├── pyproject.toml          # 项目配置和依赖（使用 uv）
├── README.md               # 项目说明文档
├── uv.lock                 # uv 依赖锁定文件
│
├── dianplus/               # 核心功能模块
│   ├── __init__.py
│   └── utils/
│       ├── __init__.py
│       └── ssl_cert_parser.py  # SSL证书解析和验证工具
│
├── tests/                  # 测试文件
│   ├── __init__.py
│   ├── test_main.py        # 主程序测试
│   └── test_ssl_cert_parser.py  # SSL证书解析器测试
│
├── k8s/                    # Kubernetes 原生部署配置
│   └── deployment.yaml     # Deployment 配置
│
└── helm/                   # Helm Chart
    └── alibaba-cloud-cert-renewer/
        ├── .helmignore     # Helm 打包忽略文件
        ├── Chart.yaml      # Chart 元数据
        ├── README.md       # Helm Chart 说明
        ├── values.yaml     # 默认配置值
        ├── values-cdn.yaml # CDN 示例配置
        ├── values-slb.yaml # SLB 示例配置
        └── templates/      # Kubernetes 资源模板
            ├── _helpers.tpl    # 辅助模板函数
            └── deployment.yaml # Deployment 模板
```

## 文件说明

### 配置文件

- **`.env`**: 本地环境变量配置（不提交到 Git）
- **`.env.example`**: 环境变量配置示例，供开发者参考
- **`.gitignore`**: Git 忽略规则，包含 Python 缓存、虚拟环境、IDE 配置等
- **`.pre-commit-config.yaml`**: pre-commit 钩子配置，自动检查代码质量
- **`.yamllint`**: YAML 文件格式检查配置
- **`pyproject.toml`**: 项目元数据、依赖管理和工具配置

### 源代码

- **`main.py`**: 主程序入口，包含配置加载、证书更新逻辑
- **`dianplus/utils/ssl_cert_parser.py`**: SSL 证书解析和验证工具

### 测试

- **`tests/test_main.py`**: 主程序功能测试
- **`tests/test_ssl_cert_parser.py`**: SSL 证书解析器测试

### 部署配置

- **`Dockerfile`**: Docker 镜像构建文件
- **`k8s/deployment.yaml`**: Kubernetes 原生部署配置
- **`helm/alibaba-cloud-cert-renewer/`**: Helm Chart 完整配置

## 忽略的文件和目录

以下文件和目录不应提交到版本控制（已在 `.gitignore` 中配置）：

- `__pycache__/`: Python 字节码缓存
- `.pytest_cache/`: pytest 测试缓存
- `.ruff_cache/`: ruff 代码检查缓存
- `.venv/`: 虚拟环境目录
- `.env`: 本地环境变量（包含敏感信息）
- `*.pyc`, `*.pyo`, `*.pyd`: Python 编译文件
- `.DS_Store`: macOS 系统文件
- IDE 配置文件（`.vscode/`, `.idea/` 等）

## 应该提交的文件

- 所有源代码文件（`.py`）
- 配置文件（`.yaml`, `.toml`, `.env.example`）
- 文档文件（`.md`）
- `uv.lock`: 依赖锁定文件，确保环境一致性
- `Dockerfile`: 容器构建文件
- Kubernetes 和 Helm 配置文件

## 项目组织原则

1. **模块化**: 核心功能放在 `dianplus/` 包中
2. **测试分离**: 测试文件独立在 `tests/` 目录
3. **部署分离**: Kubernetes 配置按部署方式分类（`k8s/` 和 `helm/`）
4. **配置集中**: 所有配置文件在根目录，便于查找
5. **文档完整**: 提供详细的 README 和示例配置
