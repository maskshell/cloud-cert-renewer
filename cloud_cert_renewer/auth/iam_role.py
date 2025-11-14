"""IAM Role凭证提供者

提供基于IAM Role的凭证获取（用于云环境中的IAM角色）。
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.auth.base import CredentialProvider


class IAMRoleCredentialProvider:
    """IAM Role凭证提供者（用于云环境中的IAM角色）"""

    def __init__(self, role_arn: str, role_session_name: str | None = None) -> None:
        """
        初始化IAM Role凭证提供者
        :param role_arn: IAM Role ARN
        :param role_session_name: 会话名称（可选）
        """
        self.role_arn = role_arn
        self.role_session_name = role_session_name or "cert-renewer-session"

    def get_credentials(self) -> Credentials:
        """
        获取IAM Role凭证
        注意：此实现需要调用云服务商的AssumeRole API
        当前仅返回占位符，实际实现需要根据云服务商进行适配
        """
        # TODO: 实现AssumeRole逻辑
        raise NotImplementedError(
            "IAM Role凭证提供者尚未实现，需要根据云服务商实现AssumeRole逻辑"
        )

