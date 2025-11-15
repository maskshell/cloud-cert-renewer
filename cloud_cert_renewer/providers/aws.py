"""AWS adapter

Implements adapter for AWS CloudFront and ELB/ALB certificate renewal
(placeholder implementation).
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter


class AWSAdapter(CloudAdapter):
    """AWS adapter (placeholder implementation)"""

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """Update AWS CloudFront certificate"""
        # TODO: Implement AWS CloudFront certificate renewal logic
        raise NotImplementedError("AWS adapter is not yet implemented")

    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """Update AWS ELB/ALB certificate"""
        # TODO: Implement AWS ELB/ALB certificate renewal logic
        raise NotImplementedError("AWS adapter is not yet implemented")

    def get_current_cdn_certificate(
        self, domain_name: str, region: str, credentials: Credentials
    ) -> str | None:
        """Get AWS CloudFront current certificate"""
        # TODO: Implement AWS CloudFront certificate query logic
        raise NotImplementedError("AWS adapter is not yet implemented")

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
    ) -> str | None:
        """Get AWS ELB/ALB current certificate fingerprint"""
        # TODO: Implement AWS ELB/ALB certificate fingerprint query logic
        raise NotImplementedError("AWS adapter is not yet implemented")
