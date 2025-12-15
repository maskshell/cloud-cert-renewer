"""Certificate renewer factory

Provides certificate renewer creation logic.
"""

from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.cert_renewer.cdn_renewer import CdnCertRenewerStrategy
from cloud_cert_renewer.cert_renewer.composite import CompositeCertRenewer
from cloud_cert_renewer.cert_renewer.load_balancer_renewer import (
    LoadBalancerCertRenewerStrategy,
)
from cloud_cert_renewer.config import AppConfig
from cloud_cert_renewer.errors import UnsupportedServiceTypeError


class CertRenewerFactory:
    """Certificate renewer factory"""

    @staticmethod
    def create(config: AppConfig) -> CompositeCertRenewer:
        """
        Create certificate renewer
        :param config: Application configuration
        :return: CompositeCertRenewer instance
        :raises ValueError: When service type is not supported
        """
        renewers: list[BaseCertRenewer] = []

        if config.service_type == "cdn":
            if config.cdn_config:
                for domain in config.cdn_config.domain_names:
                    renewers.append(CdnCertRenewerStrategy(config, domain))
        elif config.service_type == "lb":
            if config.lb_config:
                for instance_id in config.lb_config.instance_ids:
                    renewers.append(
                        LoadBalancerCertRenewerStrategy(config, instance_id)
                    )
        else:
            raise UnsupportedServiceTypeError(
                f"Unsupported service type: {config.service_type}"
            )

        return CompositeCertRenewer(renewers)
