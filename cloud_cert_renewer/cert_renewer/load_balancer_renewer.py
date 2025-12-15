"""Load Balancer certificate renewal strategy

Implements specific strategy for Load Balancer certificate renewal.
"""

import logging

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.providers.base import CloudAdapterFactory
from cloud_cert_renewer.utils.ssl_cert_parser import (
    get_cert_fingerprint_sha1,
    normalize_hex_fingerprint,
)

logger = logging.getLogger(__name__)


class LoadBalancerCertRenewerStrategy(BaseCertRenewer):
    """Load Balancer certificate renewal strategy"""

    def __init__(self, config, target_instance_id: str) -> None:
        super().__init__(config)
        self.target_instance_id = target_instance_id

    def _get_cert_info(self) -> tuple[str, str, str]:
        """Get Load Balancer certificate information"""
        if not self.config.lb_config:
            raise ValueError("Load Balancer configuration does not exist")
        return (
            self.config.lb_config.cert,
            self.config.lb_config.cert_private_key,
            self.target_instance_id,
        )

    def _validate_cert(self, cert: str, instance_id: str) -> bool:
        """
        Validate Load Balancer certificate
        (LB does not require domain validation, only certificate format validation)
        """
        # LB certificates do not require domain validation,
        # only certificate format validation
        try:
            x509.load_pem_x509_certificate(cert.encode(), default_backend())
            return True
        except Exception as e:
            logger.warning("Certificate format validation failed: %s", e)
            return False

    def _calculate_fingerprint(self, cert: str) -> str:
        """Calculate Load Balancer certificate fingerprint (SHA1)"""
        return get_cert_fingerprint_sha1(cert)

    def get_current_cert_fingerprint(self) -> str | None:
        """Get current Load Balancer certificate fingerprint"""
        if not self.config.lb_config:
            return None

        adapter = CloudAdapterFactory.create(self.config.cloud_provider)
        fingerprint = adapter.get_current_lb_certificate_fingerprint(
            instance_id=self.target_instance_id,
            listener_port=self.config.lb_config.listener_port,
            region=self.config.lb_config.region,
            credentials=self.config.credentials,
            auth_method=self.config.auth_method,
        )
        if fingerprint:
            return normalize_hex_fingerprint(fingerprint)
        return None

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """Execute Load Balancer certificate renewal"""
        if not self.config.lb_config:
            raise ValueError("Load Balancer configuration does not exist")

        adapter = CloudAdapterFactory.create(self.config.cloud_provider)
        return adapter.update_load_balancer_certificate(
            instance_id=self.target_instance_id,
            listener_port=self.config.lb_config.listener_port,
            cert=cert,
            cert_private_key=cert_private_key,
            region=self.config.lb_config.region,
            credentials=self.config.credentials,
            auth_method=self.config.auth_method,
        )
