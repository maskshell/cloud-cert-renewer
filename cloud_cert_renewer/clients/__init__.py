"""Client module

Provides cloud service provider client wrappers and factories.
"""

from cloud_cert_renewer.clients.alibaba import (
    CdnCertRenewer,
    LoadBalancerCertRenewer,
)

# Backward compatibility: Keep old class names as aliases
CdnCertsRenewer = CdnCertRenewer  # noqa: N816
SlbCertsRenewer = LoadBalancerCertRenewer  # noqa: N816

__all__ = [
    "CdnCertRenewer",
    "CdnCertsRenewer",
    "LoadBalancerCertRenewer",
    "SlbCertsRenewer",
]
