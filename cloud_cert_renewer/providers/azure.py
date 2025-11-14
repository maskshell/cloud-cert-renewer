"""Azure适配器

实现Azure CDN和Load Balancer证书更新的适配器（占位符实现）。
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter


class AzureAdapter(CloudAdapter):
    """Azure适配器（占位符实现）"""

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """更新Azure CDN证书"""
        # TODO: 实现Azure CDN证书更新逻辑
        raise NotImplementedError("Azure适配器尚未实现")

    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """更新Azure Load Balancer证书"""
        # TODO: 实现Azure Load Balancer证书更新逻辑
        raise NotImplementedError("Azure适配器尚未实现")

    def get_current_cdn_certificate(
        self, domain_name: str, region: str, credentials: Credentials
    ) -> str | None:
        """获取Azure CDN当前证书"""
        # TODO: 实现Azure CDN证书查询逻辑
        raise NotImplementedError("Azure适配器尚未实现")

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
    ) -> str | None:
        """获取Azure Load Balancer当前证书指纹"""
        # TODO: 实现Azure Load Balancer证书指纹查询逻辑
        raise NotImplementedError("Azure适配器尚未实现")

