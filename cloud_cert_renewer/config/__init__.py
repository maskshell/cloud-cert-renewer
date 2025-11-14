"""配置管理模块

提供配置对象的定义和加载逻辑，支持多云和多种鉴权方式。
"""

from cloud_cert_renewer.config import loader
from cloud_cert_renewer.config import models

# 从子模块导入
ConfigError = loader.ConfigError
load_config = loader.load_config

AppConfig = models.AppConfig
CdnConfig = models.CdnConfig
Credentials = models.Credentials
LoadBalancerConfig = models.LoadBalancerConfig

__all__ = [
    "AppConfig",
    "CdnConfig",
    "ConfigError",
    "Credentials",
    "LoadBalancerConfig",
    "load_config",
]

