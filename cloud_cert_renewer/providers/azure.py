"""Azure adapter

Implements adapter for Azure CDN and Load Balancer certificate renewal
(placeholder implementation).
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter


class AzureAdapter(CloudAdapter):
    """Azure adapter (placeholder implementation)"""

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """Update Azure CDN certificate"""
        # TODO: Implement Azure CDN certificate renewal logic
        raise NotImplementedError("Azure adapter is not yet implemented")

    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """Update Azure Load Balancer certificate"""
        # TODO: Implement Azure Load Balancer certificate renewal logic
        raise NotImplementedError("Azure adapter is not yet implemented")

    def get_current_cdn_certificate(
        self, domain_name: str, region: str, credentials: Credentials
    ) -> str | None:
        """Get Azure CDN current certificate"""
        # TODO: Implement Azure CDN certificate query logic
        raise NotImplementedError("Azure adapter is not yet implemented")

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
    ) -> str | None:
        """Get Azure Load Balancer current certificate fingerprint"""
        # TODO: Implement Azure Load Balancer certificate fingerprint query logic
        raise NotImplementedError("Azure adapter is not yet implemented")
