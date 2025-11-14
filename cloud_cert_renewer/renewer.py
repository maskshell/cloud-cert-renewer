"""证书更新器模块（向后兼容）

此文件保留用于向后兼容，实际实现已移至 cloud_cert_renewer.cert_renewer 子模块。
"""

# 向后兼容：从新模块导入所有内容
from cloud_cert_renewer.cert_renewer import (  # noqa: F401
    BaseCertRenewer,
    CertRenewerFactory,
    CertValidationError,
    CdnCertRenewerStrategy,
    LoadBalancerCertRenewerStrategy,
)

# 向后兼容：保留旧的接口名称
CertRenewerStrategy = BaseCertRenewer  # noqa: N816

__all__ = [
    "BaseCertRenewer",
    "CertRenewerFactory",
    "CertRenewerStrategy",
    "CertValidationError",
    "CdnCertRenewerStrategy",
    "LoadBalancerCertRenewerStrategy",
]
