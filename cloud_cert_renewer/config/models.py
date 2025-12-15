"""Configuration data models

Defines data classes related to configuration.
"""

from dataclasses import dataclass, field
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

    domain_names: list[str]
    cert: str
    cert_private_key: str
    region: str = "cn-hangzhou"


@dataclass
class LoadBalancerConfig:
    """Load Balancer configuration (formerly SLB)"""

    instance_ids: list[str]
    listener_port: int
    cert: str
    cert_private_key: str
    region: str = "cn-hangzhou"


@dataclass
class WebhookConfig:
    """Webhook notification configuration"""

    url: str | None = None
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    enabled_events: set[str] = field(
        default_factory=lambda: {
            "renewal_started",
            "renewal_success",
            "renewal_failed",
            "renewal_skipped",
            "batch_completed",
        }
    )


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
    # Webhook configuration
    webhook_config: WebhookConfig | None = None

    def __post_init__(self) -> None:
        """Configuration validation"""
        if self.service_type == "cdn" and not self.cdn_config:
            raise ValueError("CDN service type must provide cdn_config")
        if self.service_type == "lb" and not self.lb_config:
            raise ValueError("LB service type must provide lb_config")

        if self.cdn_config and not self.cdn_config.domain_names:
            raise ValueError("CDN config must contain at least one domain name")

        if self.lb_config and not self.lb_config.instance_ids:
            raise ValueError("LB config must contain at least one instance ID")
