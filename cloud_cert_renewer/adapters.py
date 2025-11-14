"""Cloud service adapter module (backward compatibility)

This file is kept for backward compatibility. The actual implementation
has been moved to the cloud_cert_renewer.providers submodule.
"""

# Backward compatibility: Import everything from the new module
from cloud_cert_renewer.providers import (  # noqa: F401
    AlibabaCloudAdapter,
    AWSAdapter,
    AzureAdapter,
    CloudAdapter,
    CloudAdapterFactory,
)

__all__ = [
    "AlibabaCloudAdapter",
    "AWSAdapter",
    "AzureAdapter",
    "CloudAdapter",
    "CloudAdapterFactory",
]
