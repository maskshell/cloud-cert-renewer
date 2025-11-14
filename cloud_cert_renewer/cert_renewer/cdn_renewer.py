"""CDN证书更新策略

实现CDN证书更新的具体策略。
"""

import logging
import sys
from importlib import import_module

from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.utils.ssl_cert_parser import (
    get_cert_fingerprint_sha256,
    is_cert_valid,
)

logger = logging.getLogger(__name__)


class CdnCertRenewerStrategy(BaseCertRenewer):
    """CDN证书更新策略"""

    def _get_cert_info(self) -> tuple[str, str, str]:
        """获取CDN证书信息"""
        if not self.config.cdn_config:
            raise ValueError("CDN配置不存在")
        return (
            self.config.cdn_config.cert,
            self.config.cdn_config.cert_private_key,
            self.config.cdn_config.domain_name,
        )

    def _validate_cert(self, cert: str, domain_name: str) -> bool:
        """验证CDN证书"""
        return is_cert_valid(cert, domain_name)

    def _calculate_fingerprint(self, cert: str) -> str:
        """计算CDN证书指纹（SHA256）"""
        return get_cert_fingerprint_sha256(cert)

    def get_current_cert_fingerprint(self) -> str | None:
        """获取CDN当前证书指纹"""
        if not self.config.cdn_config:
            return None

        # 延迟导入避免循环依赖
        # 动态导入clients模块
        if "cloud_cert_renewer.clients.alibaba" not in sys.modules:
            clients_module = import_module("cloud_cert_renewer.clients.alibaba")
        else:
            clients_module = sys.modules["cloud_cert_renewer.clients.alibaba"]

        CdnCertRenewer = getattr(clients_module, "CdnCertRenewer")

        current_cert = CdnCertRenewer.get_current_cert(
            domain_name=self.config.cdn_config.domain_name,
            access_key_id=self.config.credentials.access_key_id,
            access_key_secret=self.config.credentials.access_key_secret,
        )
        if current_cert:
            return get_cert_fingerprint_sha256(current_cert)
        return None

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """执行CDN证书更新"""
        if not self.config.cdn_config:
            raise ValueError("CDN配置不存在")

        # 延迟导入避免循环依赖
        # 动态导入clients模块
        if "cloud_cert_renewer.clients.alibaba" not in sys.modules:
            clients_module = import_module("cloud_cert_renewer.clients.alibaba")
        else:
            clients_module = sys.modules["cloud_cert_renewer.clients.alibaba"]

        CdnCertRenewer = getattr(clients_module, "CdnCertRenewer")

        return CdnCertRenewer.renew_cert(
            domain_name=self.config.cdn_config.domain_name,
            cert=cert,
            cert_private_key=cert_private_key,
            region=self.config.cdn_config.region,
            access_key_id=self.config.credentials.access_key_id,
            access_key_secret=self.config.credentials.access_key_secret,
            force=self.config.force_update,
        )

