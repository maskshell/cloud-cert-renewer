"""鉴权提供者基类

定义鉴权提供者的抽象接口。
"""

from typing import Protocol

from cloud_cert_renewer.config import Credentials


class CredentialProvider(Protocol):
    """凭证提供者协议接口"""

    def get_credentials(self) -> Credentials:
        """
        获取凭证
        :return: Credentials对象
        :raises ValueError: 当无法获取凭证时抛出
        """
        ...  # noqa: UP007

