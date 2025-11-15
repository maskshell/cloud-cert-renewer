"""Load Balancer certificate renewal strategy

Implements specific strategy for Load Balancer certificate renewal.
"""

import logging
import sys
from importlib import import_module

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from cloud_cert_renewer.auth.factory import CredentialProviderFactory
from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.utils.ssl_cert_parser import get_cert_fingerprint_sha1

logger = logging.getLogger(__name__)


class LoadBalancerCertRenewerStrategy(BaseCertRenewer):
    """Load Balancer certificate renewal strategy"""

    def _get_cert_info(self) -> tuple[str, str, str]:
        """Get Load Balancer certificate information"""
        if not self.config.lb_config:
            raise ValueError("Load Balancer configuration does not exist")
        return (
            self.config.lb_config.cert,
            self.config.lb_config.cert_private_key,
            self.config.lb_config.instance_id,
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

        # Create credential provider and get credential client
        provider = CredentialProviderFactory.create(
            auth_method=self.config.auth_method, credentials=self.config.credentials
        )
        credential_client = provider.get_credential_client()

        # Lazy import to avoid circular dependencies
        # Dynamically import clients module
        if "cloud_cert_renewer.clients.alibaba" not in sys.modules:
            clients_module = import_module("cloud_cert_renewer.clients.alibaba")
        else:
            clients_module = sys.modules["cloud_cert_renewer.clients.alibaba"]

        load_balancer_cert_renewer = getattr(clients_module, "LoadBalancerCertRenewer")

        return load_balancer_cert_renewer.get_current_cert_fingerprint(
            instance_id=self.config.lb_config.instance_id,
            listener_port=self.config.lb_config.listener_port,
            region=self.config.lb_config.region,
            credential_client=credential_client,
        )

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """Execute Load Balancer certificate renewal"""
        if not self.config.lb_config:
            raise ValueError("Load Balancer configuration does not exist")

        # Create credential provider and get credential client
        provider = CredentialProviderFactory.create(
            auth_method=self.config.auth_method, credentials=self.config.credentials
        )
        credential_client = provider.get_credential_client()

        # Lazy import to avoid circular dependencies
        # Dynamically import clients module
        if "cloud_cert_renewer.clients.alibaba" not in sys.modules:
            clients_module = import_module("cloud_cert_renewer.clients.alibaba")
        else:
            clients_module = sys.modules["cloud_cert_renewer.clients.alibaba"]

        load_balancer_cert_renewer = getattr(clients_module, "LoadBalancerCertRenewer")

        return load_balancer_cert_renewer.renew_cert(
            instance_id=self.config.lb_config.instance_id,
            listener_port=self.config.lb_config.listener_port,
            cert=cert,
            cert_private_key=cert_private_key,
            region=self.config.lb_config.region,
            credential_client=credential_client,
            force=self.config.force_update,
        )
