"""CDN certificate renewal strategy

Implements specific strategy for CDN certificate renewal.
"""

import logging

from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.providers.base import CloudAdapterFactory
from cloud_cert_renewer.utils.ssl_cert_parser import (
    get_cert_fingerprint_sha256,
    is_cert_valid,
)

logger = logging.getLogger(__name__)


class CdnCertRenewerStrategy(BaseCertRenewer):
    """CDN certificate renewal strategy"""

    def __init__(self, config, target_domain: str) -> None:
        super().__init__(config)
        self.target_domain = target_domain

    def _get_cert_info(self) -> tuple[str, str, str]:
        """Get CDN certificate information"""
        if not self.config.cdn_config:
            raise ValueError("CDN configuration does not exist")
        return (
            self.config.cdn_config.cert,
            self.config.cdn_config.cert_private_key,
            self.target_domain,
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

        adapter = CloudAdapterFactory.create(self.config.cloud_provider)
        current_cert = adapter.get_current_cdn_certificate(
            domain_name=self.target_domain,
            region=self.config.cdn_config.region,
            credentials=self.config.credentials,
            auth_method=self.config.auth_method,
        )
        if current_cert:
            return get_cert_fingerprint_sha256(current_cert)
        return None

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """Execute CDN certificate renewal"""
        if not self.config.cdn_config:
            raise ValueError("CDN configuration does not exist")

        adapter = CloudAdapterFactory.create(self.config.cloud_provider)
        return adapter.update_cdn_certificate(
            domain_name=self.target_domain,
            cert=cert,
            cert_private_key=cert_private_key,
            region=self.config.cdn_config.region,
            credentials=self.config.credentials,
            auth_method=self.config.auth_method,
        )
