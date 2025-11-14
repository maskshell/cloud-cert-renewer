"""Configuration management module (backward compatibility)

This file is kept for backward compatibility. The actual implementation
has been moved to the cloud_cert_renewer.config submodule.
"""

# Backward compatibility: Import everything from the new module
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
