"""配置数据模型

定义配置相关的数据类。
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Credentials:
    """凭证数据类"""

    access_key_id: str
    access_key_secret: str
    security_token: str | None = None  # 用于STS临时凭证


@dataclass
class CdnConfig:
    """CDN配置"""

    domain_name: str
    cert: str
    cert_private_key: str
    region: str = "cn-hangzhou"


@dataclass
class LoadBalancerConfig:
    """负载均衡器配置（原SLB）"""

    instance_id: str
    listener_port: int
    cert: str
    cert_private_key: str
    region: str = "cn-hangzhou"


@dataclass
class AppConfig:
    """应用配置"""

    service_type: Literal["cdn", "lb"]
    cloud_provider: str  # 云服务提供商：alibaba, aws, azure等
    auth_method: str  # 鉴权方式：access_key, sts, iam_role, service_account, env
    credentials: Credentials
    force_update: bool = False
    # 服务特定配置
    cdn_config: CdnConfig | None = None
    lb_config: LoadBalancerConfig | None = None

    def __post_init__(self) -> None:
        """配置验证"""
        if self.service_type == "cdn" and not self.cdn_config:
            raise ValueError("CDN服务类型必须提供cdn_config")
        if self.service_type == "lb" and not self.lb_config:
            raise ValueError("LB服务类型必须提供lb_config")

