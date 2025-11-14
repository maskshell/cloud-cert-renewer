"""ServiceAccount凭证提供者

提供基于Kubernetes ServiceAccount的凭证获取。
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.auth.base import CredentialProvider


class ServiceAccountCredentialProvider:
    """ServiceAccount凭证提供者（用于Kubernetes环境）"""

    def __init__(
        self,
        service_account_path: str = "/var/run/secrets/kubernetes.io/serviceaccount",
    ) -> None:
        """
        初始化ServiceAccount凭证提供者
        :param service_account_path: ServiceAccount token路径
        """
        self.service_account_path = service_account_path

    def get_credentials(self) -> Credentials:
        """
        获取ServiceAccount凭证
        注意：此实现需要从Kubernetes ServiceAccount读取token并调用云服务商API
        当前仅返回占位符，实际实现需要根据云服务商进行适配
        """
        # TODO: 实现ServiceAccount token读取和云服务商API调用逻辑
        raise NotImplementedError(
            "ServiceAccount凭证提供者尚未实现，需要根据云服务商实现token读取和API调用逻辑"
        )

