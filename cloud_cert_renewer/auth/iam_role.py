"""IAM Role credential provider

Provides credential retrieval based on IAM Role (for IAM roles in cloud environments).
"""

from cloud_cert_renewer.config import Credentials


class IAMRoleCredentialProvider:
    """IAM Role credential provider (for IAM roles in cloud environments)"""

    def __init__(self, role_arn: str, role_session_name: str | None = None) -> None:
        """
        Initialize IAM Role credential provider
        :param role_arn: IAM Role ARN
        :param role_session_name: Session name (optional)
        """
        self.role_arn = role_arn
        self.role_session_name = role_session_name or "cert-renewer-session"

    def get_credentials(self) -> Credentials:
        """
        Get IAM Role credentials
        Note: This implementation needs to call the cloud provider's AssumeRole API
        Currently only returns a placeholder, actual implementation needs to be
        adapted based on cloud provider
        """
        # TODO: Implement AssumeRole logic
        raise NotImplementedError(
            "IAM Role credential provider is not yet implemented, "
            "needs to implement AssumeRole logic based on cloud provider"
        )
