"""负载均衡器证书更新策略

实现负载均衡器证书更新的具体策略。
"""

import logging
import sys
from importlib import import_module

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.utils.ssl_cert_parser import get_cert_fingerprint_sha1

logger = logging.getLogger(__name__)


class LoadBalancerCertRenewerStrategy(BaseCertRenewer):
    """负载均衡器证书更新策略"""

    def _get_cert_info(self) -> tuple[str, str, str]:
        """获取负载均衡器证书信息"""
        if not self.config.lb_config:
            raise ValueError("负载均衡器配置不存在")
        return (
            self.config.lb_config.cert,
            self.config.lb_config.cert_private_key,
            self.config.lb_config.instance_id,
        )

    def _validate_cert(self, cert: str, instance_id: str) -> bool:
        """验证负载均衡器证书（LB不需要域名验证，只验证证书格式）"""
        # LB证书不需要域名验证，只需要验证证书格式
        try:
            x509.load_pem_x509_certificate(cert.encode(), default_backend())
            return True
        except Exception as e:
            logger.warning("证书格式验证失败: %s", e)
            return False

    def _calculate_fingerprint(self, cert: str) -> str:
        """计算负载均衡器证书指纹（SHA1）"""
        return get_cert_fingerprint_sha1(cert)

    def get_current_cert_fingerprint(self) -> str | None:
        """获取负载均衡器当前证书指纹"""
        if not self.config.lb_config:
            return None

        # 延迟导入避免循环依赖
        # 动态导入clients模块
        if "cloud_cert_renewer.clients.alibaba" not in sys.modules:
            clients_module = import_module("cloud_cert_renewer.clients.alibaba")
        else:
            clients_module = sys.modules["cloud_cert_renewer.clients.alibaba"]

        LoadBalancerCertRenewer = getattr(clients_module, "LoadBalancerCertRenewer")

        return LoadBalancerCertRenewer.get_current_cert_fingerprint(
            instance_id=self.config.lb_config.instance_id,
            listener_port=self.config.lb_config.listener_port,
            region=self.config.lb_config.region,
            access_key_id=self.config.credentials.access_key_id,
            access_key_secret=self.config.credentials.access_key_secret,
        )

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """执行负载均衡器证书更新"""
        if not self.config.lb_config:
            raise ValueError("负载均衡器配置不存在")

        # 延迟导入避免循环依赖
        # 动态导入clients模块
        if "cloud_cert_renewer.clients.alibaba" not in sys.modules:
            clients_module = import_module("cloud_cert_renewer.clients.alibaba")
        else:
            clients_module = sys.modules["cloud_cert_renewer.clients.alibaba"]

        LoadBalancerCertRenewer = getattr(clients_module, "LoadBalancerCertRenewer")

        return LoadBalancerCertRenewer.renew_cert(
            instance_id=self.config.lb_config.instance_id,
            listener_port=self.config.lb_config.listener_port,
            cert=cert,
            cert_private_key=cert_private_key,
            region=self.config.lb_config.region,
            access_key_id=self.config.credentials.access_key_id,
            access_key_secret=self.config.credentials.access_key_secret,
            force=self.config.force_update,
        )

