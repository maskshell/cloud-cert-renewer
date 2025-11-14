"""云服务适配器模块（向后兼容）

此文件保留用于向后兼容，实际实现已移至 cloud_cert_renewer.providers 子模块。
"""

# 向后兼容：从新模块导入所有内容
from cloud_cert_renewer.providers import (  # noqa: F401
    AlibabaCloudAdapter,
    AWSAdapter,
    AzureAdapter,
    CloudAdapter,
    CloudAdapterFactory,
)

__all__ = [
    "AlibabaCloudAdapter",
    "AWSAdapter",
    "AzureAdapter",
    "CloudAdapter",
    "CloudAdapterFactory",
]
