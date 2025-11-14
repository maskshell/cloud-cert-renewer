"""云服务提供商适配器基类

定义云服务提供商适配器的抽象接口和工厂。
"""

import logging
from abc import ABC, abstractmethod

from cloud_cert_renewer.config import Credentials

logger = logging.getLogger(__name__)


class CloudAdapter(ABC):
    """云服务适配器接口"""

    @abstractmethod
    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """
        更新CDN证书
        :param domain_name: 域名
        :param cert: 证书内容
        :param cert_private_key: 证书私钥
        :param region: 区域
        :param credentials: 凭证
        :return: 是否成功
        """
        pass

    @abstractmethod
    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
    ) -> bool:
        """
        更新负载均衡器证书
        :param instance_id: 实例ID
        :param listener_port: 监听器端口
        :param cert: 证书内容
        :param cert_private_key: 证书私钥
        :param region: 区域
        :param credentials: 凭证
        :return: 是否成功
        """
        pass

    @abstractmethod
    def get_current_cdn_certificate(
        self, domain_name: str, region: str, credentials: Credentials
    ) -> str | None:
        """
        获取当前CDN证书
        :param domain_name: 域名
        :param region: 区域
        :param credentials: 凭证
        :return: 证书内容，如果查询失败则返回None
        """
        pass

    @abstractmethod
    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
    ) -> str | None:
        """
        获取当前负载均衡器证书指纹
        :param instance_id: 实例ID
        :param listener_port: 监听器端口
        :param region: 区域
        :param credentials: 凭证
        :return: 证书指纹，如果查询失败则返回None
        """
        pass


class CloudAdapterFactory:
    """云服务适配器工厂"""

    _adapters: dict[str, type[CloudAdapter]] = {}

    @classmethod
    def _register_default_adapters(cls) -> None:
        """注册默认适配器"""
        if not cls._adapters:
            from cloud_cert_renewer.providers.alibaba import AlibabaCloudAdapter
            from cloud_cert_renewer.providers.aws import AWSAdapter
            from cloud_cert_renewer.providers.azure import AzureAdapter

            cls._adapters = {
                "alibaba": AlibabaCloudAdapter,
                "aws": AWSAdapter,
                "azure": AzureAdapter,
            }

    @classmethod
    def create(cls, cloud_provider: str) -> CloudAdapter:
        """
        创建云服务适配器
        :param cloud_provider: 云服务提供商（alibaba, aws, azure等）
        :return: CloudAdapter实例
        :raises ValueError: 当云服务提供商不支持时抛出
        """
        cls._register_default_adapters()
        cloud_provider = cloud_provider.lower()
        adapter_class = cls._adapters.get(cloud_provider)
        if not adapter_class:
            raise ValueError(
                f"不支持的云服务提供商: {cloud_provider}，支持: {', '.join(cls._adapters.keys())}"
            )
        return adapter_class()

    @classmethod
    def register_adapter(
        cls, cloud_provider: str, adapter_class: type[CloudAdapter]
    ) -> None:
        """
        注册自定义适配器
        :param cloud_provider: 云服务提供商名称
        :param adapter_class: 适配器类
        """
        cls._adapters[cloud_provider.lower()] = adapter_class
        logger.info("注册云服务适配器: %s", cloud_provider)

