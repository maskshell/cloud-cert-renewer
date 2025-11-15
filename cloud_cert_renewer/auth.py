"""Authentication module (backward compatibility)

This file is kept for backward compatibility, actual implementation has been moved to
cloud_cert_renewer.auth submodules.
"""

# Backward compatibility: import everything from new modules
from cloud_cert_renewer.auth import (  # noqa: F401
    AccessKeyCredentialProvider,
    CredentialProvider,
    CredentialProviderFactory,
    EnvCredentialProvider,
    IAMRoleCredentialProvider,
    ServiceAccountCredentialProvider,
    STSCredentialProvider,
)

__all__ = [
    "AccessKeyCredentialProvider",
    "CredentialProvider",
    "CredentialProviderFactory",
    "EnvCredentialProvider",
    "IAMRoleCredentialProvider",
    "ServiceAccountCredentialProvider",
    "STSCredentialProvider",
]
