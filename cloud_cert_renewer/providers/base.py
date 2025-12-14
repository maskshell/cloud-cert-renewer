"""Cloud service provider adapter base class

Defines abstract interfaces and factories for cloud service provider adapters.
"""

import logging
from abc import ABC, abstractmethod

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.errors import UnsupportedCloudProviderError

logger = logging.getLogger(__name__)


class CloudAdapter(ABC):
    """Cloud service adapter interface"""

    @abstractmethod
    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> bool:
        """
        Update CDN certificate
        :param domain_name: Domain name
        :param cert: Certificate content
        :param cert_private_key: Certificate private key
        :param region: Region
        :param credentials: Credentials
        :param auth_method: Authentication method (optional)
        :return: Whether successful
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
        auth_method: str | None = None,
    ) -> bool:
        """
        Update Load Balancer certificate
        :param instance_id: Instance ID
        :param listener_port: Listener port
        :param cert: Certificate content
        :param cert_private_key: Certificate private key
        :param region: Region
        :param credentials: Credentials
        :param auth_method: Authentication method (optional)
        :return: Whether successful
        """
        pass

    @abstractmethod
    def get_current_cdn_certificate(
        self,
        domain_name: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> str | None:
        """
        Get current CDN certificate
        :param domain_name: Domain name
        :param region: Region
        :param credentials: Credentials
        :param auth_method: Authentication method (optional)
        :return: Certificate content, or None if query fails
        """
        pass

    @abstractmethod
    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> str | None:
        """
        Get current Load Balancer certificate fingerprint
        :param instance_id: Instance ID
        :param listener_port: Listener port
        :param region: Region
        :param credentials: Credentials
        :param auth_method: Authentication method (optional)
        :return: Certificate fingerprint, or None if query fails
        """
        pass


class CloudAdapterFactory:
    """Cloud service adapter factory"""

    _adapters: dict[str, type[CloudAdapter]] = {}

    @classmethod
    def _register_default_adapters(cls) -> None:
        """Register default adapters"""
        from cloud_cert_renewer.providers.alibaba import AlibabaCloudAdapter
        from cloud_cert_renewer.providers.aws import AWSAdapter
        from cloud_cert_renewer.providers.azure import AzureAdapter
        from cloud_cert_renewer.providers.noop import NoopAdapter

        defaults: dict[str, type[CloudAdapter]] = {
            "alibaba": AlibabaCloudAdapter,
            "aws": AWSAdapter,
            "azure": AzureAdapter,
            "noop": NoopAdapter,
        }

        # Merge defaults without overwriting any adapters already registered.
        for name, adapter in defaults.items():
            cls._adapters.setdefault(name, adapter)

    @classmethod
    def create(cls, cloud_provider: str) -> CloudAdapter:
        """
        Create cloud service adapter
        :param cloud_provider: Cloud service provider (alibaba, aws, azure, etc.)
        :return: CloudAdapter instance
        :raises ValueError: Raises when cloud service provider is not supported
        """
        cls._register_default_adapters()
        cloud_provider = cloud_provider.lower()
        adapter_class = cls._adapters.get(cloud_provider)
        if not adapter_class:
            supported = ", ".join(cls._adapters.keys())
            raise UnsupportedCloudProviderError(
                f"Unsupported cloud service provider: {cloud_provider}, "
                f"supported: {supported}"
            )
        return adapter_class()

    @classmethod
    def register_adapter(
        cls, cloud_provider: str, adapter_class: type[CloudAdapter]
    ) -> None:
        """
        Register custom adapter
        :param cloud_provider: Cloud service provider name
        :param adapter_class: Adapter class
        """
        cls._register_default_adapters()
        cls._adapters[cloud_provider.lower()] = adapter_class
        logger.info("Registered cloud service adapter: %s", cloud_provider)
