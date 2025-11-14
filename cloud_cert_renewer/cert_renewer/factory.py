"""Certificate renewer factory

Provides certificate renewer creation logic.
"""

from cloud_cert_renewer.config import AppConfig
from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.cert_renewer.cdn_renewer import CdnCertRenewerStrategy
from cloud_cert_renewer.cert_renewer.load_balancer_renewer import (
    LoadBalancerCertRenewerStrategy,
)


class CertRenewerFactory:
    """Certificate renewer factory"""

    @staticmethod
    def create(config: AppConfig) -> BaseCertRenewer:
        """
        Create certificate renewer
        :param config: Application configuration
        :return: BaseCertRenewer instance
        :raises ValueError: When service type is not supported
        """
        if config.service_type == "cdn":
            return CdnCertRenewerStrategy(config)
        elif config.service_type == "lb":
            return LoadBalancerCertRenewerStrategy(config)
        else:
            raise ValueError(f"Unsupported service type: {config.service_type}")
