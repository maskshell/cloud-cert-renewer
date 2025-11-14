"""Alibaba Cloud adapter

Implements adapter for Alibaba Cloud CDN and Load Balancer certificate renewal.
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter


class AlibabaCloudAdapter(CloudAdapter):
    """Alibaba Cloud adapter (Alibaba Cloud Adapter)"""

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """Update Alibaba Cloud CDN certificate (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import CdnCertRenewer

        return CdnCertRenewer.renew_cert(
            domain_name=domain_name,
            cert=cert,
            cert_private_key=cert_private_key,
            region=region,
            access_key_id=credentials.access_key_id,
            access_key_secret=credentials.access_key_secret,
            force=False,
        )

    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """Update Alibaba Cloud Load Balancer certificate (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import LoadBalancerCertRenewer

        return LoadBalancerCertRenewer.renew_cert(
            instance_id=instance_id,
            listener_port=listener_port,
            cert=cert,
            cert_private_key=cert_private_key,
            region=region,
            access_key_id=credentials.access_key_id,
            access_key_secret=credentials.access_key_secret,
            force=False,
        )

    def get_current_cdn_certificate(
        self, domain_name: str, region: str, credentials: Credentials
    ) -> str | None:
        """Get Alibaba Cloud CDN current certificate (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import CdnCertRenewer

        return CdnCertRenewer.get_current_cert(
            domain_name=domain_name,
            access_key_id=credentials.access_key_id,
            access_key_secret=credentials.access_key_secret,
        )

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
    ) -> str | None:
        """Get Alibaba Cloud Load Balancer current certificate fingerprint (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import LoadBalancerCertRenewer

        return LoadBalancerCertRenewer.get_current_cert_fingerprint(
            instance_id=instance_id,
            listener_port=listener_port,
            region=region,
            access_key_id=credentials.access_key_id,
            access_key_secret=credentials.access_key_secret,
        )
