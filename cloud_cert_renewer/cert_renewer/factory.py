"""证书更新器工厂

提供证书更新器的创建逻辑。
"""

from cloud_cert_renewer.config import AppConfig
from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.cert_renewer.cdn_renewer import CdnCertRenewerStrategy
from cloud_cert_renewer.cert_renewer.load_balancer_renewer import (
    LoadBalancerCertRenewerStrategy,
)


class CertRenewerFactory:
    """证书更新器工厂"""

    @staticmethod
    def create(config: AppConfig) -> BaseCertRenewer:
        """
        创建证书更新器
        :param config: 应用配置
        :return: BaseCertRenewer实例
        :raises ValueError: 当服务类型不支持时抛出
        """
        if config.service_type == "cdn":
            return CdnCertRenewerStrategy(config)
        elif config.service_type == "lb":
            return LoadBalancerCertRenewerStrategy(config)
        else:
            raise ValueError(f"不支持的服务类型: {config.service_type}")

