"""客户端模块

提供云服务商客户端的封装和工厂。
"""

from cloud_cert_renewer.clients.alibaba import (
    CdnCertRenewer,
    LoadBalancerCertRenewer,
)

# 向后兼容：保留旧的类名作为别名
CdnCertsRenewer = CdnCertRenewer  # noqa: N816
SlbCertsRenewer = LoadBalancerCertRenewer  # noqa: N816

__all__ = [
    "CdnCertRenewer",
    "CdnCertsRenewer",
    "LoadBalancerCertRenewer",
    "SlbCertsRenewer",
]

