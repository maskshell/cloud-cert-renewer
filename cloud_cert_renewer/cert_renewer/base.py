"""证书更新器基类

定义证书更新器的抽象接口和模板方法。
"""

import logging
from abc import ABC, abstractmethod

from cloud_cert_renewer.config import AppConfig

logger = logging.getLogger(__name__)


class CertValidationError(Exception):
    """证书验证错误异常"""

    pass


class BaseCertRenewer(ABC):
    """证书更新器基类（模板方法模式）"""

    def __init__(self, config: AppConfig) -> None:
        """
        初始化证书更新器
        :param config: 应用配置
        """
        self.config = config

    def renew(self) -> bool:
        """
        更新证书（模板方法）
        定义了证书更新的标准流程：
        1. 验证证书
        2. 比较证书指纹（如果不需要强制更新）
        3. 执行更新
        :return: 是否成功
        """
        # 获取证书和私钥
        cert, cert_private_key, domain_or_instance = self._get_cert_info()

        # 步骤1：验证证书
        if not self._validate_cert(cert, domain_or_instance):
            raise CertValidationError(
                f"证书验证失败：域名 {domain_or_instance} 不在证书中或证书已过期"
            )

        # 步骤2：比较证书指纹（如果不需要强制更新）
        if not self.config.force_update:
            current_fingerprint = self.get_current_cert_fingerprint()
            if current_fingerprint:
                new_fingerprint = self._calculate_fingerprint(cert)
                if new_fingerprint == current_fingerprint:
                    logger.info(
                        "证书未变化，跳过更新: %s, 指纹=%s",
                        domain_or_instance,
                        new_fingerprint[:20] + "...",
                    )
                    return True
        else:
            logger.info(
                "强制更新模式已启用，即使证书相同也会更新: %s", domain_or_instance
            )

        # 步骤3：执行更新
        return self._do_renew(cert, cert_private_key)

    @abstractmethod
    def _get_cert_info(self) -> tuple[str, str, str]:
        """
        获取证书信息
        :return: (cert, cert_private_key, domain_or_instance)
        """
        pass

    @abstractmethod
    def _validate_cert(self, cert: str, domain_or_instance: str) -> bool:
        """
        验证证书
        :param cert: 证书内容
        :param domain_or_instance: 域名或实例ID
        :return: 是否有效
        """
        pass

    @abstractmethod
    def _calculate_fingerprint(self, cert: str) -> str:
        """
        计算证书指纹
        :param cert: 证书内容
        :return: 证书指纹
        """
        pass

    @abstractmethod
    def get_current_cert_fingerprint(self) -> str | None:
        """
        获取当前证书指纹
        :return: 证书指纹，如果查询失败则返回None
        """
        pass

    @abstractmethod
    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """
        执行证书更新（子类实现具体逻辑）
        :param cert: 证书内容
        :param cert_private_key: 证书私钥
        :return: 是否成功
        """
        pass

