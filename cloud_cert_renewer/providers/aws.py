"""AWS适配器

实现AWS CloudFront和ELB/ALB证书更新的适配器（占位符实现）。
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter


class AWSAdapter(CloudAdapter):
    """AWS适配器（占位符实现）"""

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """更新AWS CloudFront证书"""
        # TODO: 实现AWS CloudFront证书更新逻辑
        raise NotImplementedError("AWS适配器尚未实现")

    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """更新AWS ELB/ALB证书"""
        # TODO: 实现AWS ELB/ALB证书更新逻辑
        raise NotImplementedError("AWS适配器尚未实现")

    def get_current_cdn_certificate(
        self, domain_name: str, region: str, credentials: Credentials
    ) -> str | None:
        """获取AWS CloudFront当前证书"""
        # TODO: 实现AWS CloudFront证书查询逻辑
        raise NotImplementedError("AWS适配器尚未实现")

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
    ) -> str | None:
        """获取AWS ELB/ALB当前证书指纹"""
        # TODO: 实现AWS ELB/ALB证书指纹查询逻辑
        raise NotImplementedError("AWS适配器尚未实现")

