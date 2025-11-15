"""Cloud service provider adapter module

Provides multi-cloud adapter interfaces and implementations,
supporting certificate renewal for different cloud service providers.
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
