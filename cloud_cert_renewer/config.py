"""配置管理模块（向后兼容）

此文件保留用于向后兼容，实际实现已移至 cloud_cert_renewer.config 子模块。
"""

# 向后兼容：从新模块导入所有内容
from cloud_cert_renewer.config import (  # noqa: F401
    AppConfig,
    CdnConfig,
    ConfigError,
    Credentials,
    LoadBalancerConfig,
    load_config,
)

__all__ = [
    "AppConfig",
    "CdnConfig",
    "ConfigError",
    "Credentials",
    "LoadBalancerConfig",
    "load_config",
]
