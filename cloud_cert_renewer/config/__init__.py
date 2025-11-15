"""Configuration management module

Provides definition and loading logic for configuration objects,
supporting multi-cloud and multiple authentication methods.
"""

from cloud_cert_renewer.config import loader, models

# Import from submodules
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
