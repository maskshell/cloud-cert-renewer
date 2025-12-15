"""Configuration data models

Defines data classes related to configuration.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Credentials:
    """Credentials data class"""

    access_key_id: str
    access_key_secret: str
    security_token: str | None = None  # For STS temporary credentials


@dataclass
class CdnConfig:
    """CDN configuration"""

    domain_name: str
    cert: str
    cert_private_key: str
    region: str = "cn-hangzhou"


@dataclass
class LoadBalancerConfig:
    """Load Balancer configuration (formerly SLB)"""

    instance_id: str
    listener_port: int
    cert: str
    cert_private_key: str
    region: str = "cn-hangzhou"


@dataclass
class AppConfig:
    """Application configuration"""

    service_type: Literal["cdn", "lb"]
    cloud_provider: str  # Cloud service provider: alibaba, aws, azure, etc.
    auth_method: (
        str  # Authentication method: access_key, sts, iam_role, service_account, env
    )
    credentials: Credentials
    force_update: bool = False
    dry_run: bool = False
    # Service-specific configuration
    cdn_config: CdnConfig | None = None
    lb_config: LoadBalancerConfig | None = None

    def __post_init__(self) -> None:
        """Configuration validation"""
        if self.service_type == "cdn" and not self.cdn_config:
            raise ValueError("CDN service type must provide cdn_config")
        if self.service_type == "lb" and not self.lb_config:
            raise ValueError("LB service type must provide lb_config")
