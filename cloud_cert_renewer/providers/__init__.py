"""云服务提供商适配器模块

提供多云适配器接口和实现，支持不同云服务商的证书更新。
"""

from cloud_cert_renewer.providers.alibaba import AlibabaCloudAdapter
from cloud_cert_renewer.providers.aws import AWSAdapter
from cloud_cert_renewer.providers.azure import AzureAdapter
from cloud_cert_renewer.providers.base import CloudAdapter, CloudAdapterFactory

__all__ = [
    "AlibabaCloudAdapter",
    "AWSAdapter",
    "AzureAdapter",
    "CloudAdapter",
    "CloudAdapterFactory",
]

