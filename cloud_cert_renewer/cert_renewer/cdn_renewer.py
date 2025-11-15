"""CDN certificate renewal strategy

Implements specific strategy for CDN certificate renewal.
"""

import logging
import sys
from importlib import import_module

from cloud_cert_renewer.auth.factory import CredentialProviderFactory
from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.utils.ssl_cert_parser import (
    get_cert_fingerprint_sha256,
    is_cert_valid,
)

logger = logging.getLogger(__name__)


class CdnCertRenewerStrategy(BaseCertRenewer):
    """CDN certificate renewal strategy"""

    def _get_cert_info(self) -> tuple[str, str, str]:
        """Get CDN certificate information"""
        if not self.config.cdn_config:
            raise ValueError("CDN configuration does not exist")
        return (
            self.config.cdn_config.cert,
            self.config.cdn_config.cert_private_key,
            self.config.cdn_config.domain_name,
        )

    def _validate_cert(self, cert: str, domain_name: str) -> bool:
        """Validate CDN certificate"""
        return is_cert_valid(cert, domain_name)

    def _calculate_fingerprint(self, cert: str) -> str:
        """Calculate CDN certificate fingerprint (SHA256)"""
        return get_cert_fingerprint_sha256(cert)

    def get_current_cert_fingerprint(self) -> str | None:
        """Get current CDN certificate fingerprint"""
        if not self.config.cdn_config:
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

        cdn_cert_renewer = getattr(clients_module, "CdnCertRenewer")

        current_cert = cdn_cert_renewer.get_current_cert(
            domain_name=self.config.cdn_config.domain_name,
            credential_client=credential_client,
        )
        if current_cert:
            return get_cert_fingerprint_sha256(current_cert)
        return None

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """Execute CDN certificate renewal"""
        if not self.config.cdn_config:
            raise ValueError("CDN configuration does not exist")

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

        cdn_cert_renewer = getattr(clients_module, "CdnCertRenewer")

        return cdn_cert_renewer.renew_cert(
            domain_name=self.config.cdn_config.domain_name,
            cert=cert,
            cert_private_key=cert_private_key,
            region=self.config.cdn_config.region,
            credential_client=credential_client,
            force=self.config.force_update,
        )
