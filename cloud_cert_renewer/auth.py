"""鉴权模块（向后兼容）

此文件保留用于向后兼容，实际实现已移至 cloud_cert_renewer.auth 子模块。
"""

# 向后兼容：从新模块导入所有内容
from cloud_cert_renewer.auth import (  # noqa: F401
    AccessKeyCredentialProvider,
    CredentialProvider,
    CredentialProviderFactory,
    EnvCredentialProvider,
    IAMRoleCredentialProvider,
    ServiceAccountCredentialProvider,
    STSCredentialProvider,
)

__all__ = [
    "AccessKeyCredentialProvider",
    "CredentialProvider",
    "CredentialProviderFactory",
    "EnvCredentialProvider",
    "IAMRoleCredentialProvider",
    "ServiceAccountCredentialProvider",
    "STSCredentialProvider",
]
