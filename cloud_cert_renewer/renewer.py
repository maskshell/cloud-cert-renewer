"""Certificate renewer module (backward compatibility)

This file is kept for backward compatibility. The actual implementation
has been moved to the cloud_cert_renewer.cert_renewer submodule.
"""

# Backward compatibility: Import everything from the new module
from cloud_cert_renewer.cert_renewer import (  # noqa: F401
    BaseCertRenewer,
    CertRenewerFactory,
    CertValidationError,
    CdnCertRenewerStrategy,
    LoadBalancerCertRenewerStrategy,
)

# Backward compatibility: Keep old interface name
CertRenewerStrategy = BaseCertRenewer  # noqa: N816

__all__ = [
    "BaseCertRenewer",
    "CertRenewerFactory",
    "CertRenewerStrategy",
    "CertValidationError",
    "CdnCertRenewerStrategy",
    "LoadBalancerCertRenewerStrategy",
]
