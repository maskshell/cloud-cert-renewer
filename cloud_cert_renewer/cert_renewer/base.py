"""Certificate renewer base class

Defines abstract interfaces and template methods for certificate renewers.
"""

import logging
from abc import ABC, abstractmethod

from cloud_cert_renewer.config import AppConfig

logger = logging.getLogger(__name__)


class CertValidationError(Exception):
    """Certificate validation error exception"""

    pass


class BaseCertRenewer(ABC):
    """Certificate renewer base class (Template Method pattern)"""

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize certificate renewer
        :param config: Application configuration
        """
        self.config = config

    def renew(self) -> bool:
        """
        Renew certificate (template method)
        Defines the standard certificate renewal process:
        1. Validate certificate
        2. Compare certificate fingerprints (if force update is not required)
        3. Execute renewal
        :return: Whether successful
        """
        # Get certificate and private key
        cert, cert_private_key, domain_or_instance = self._get_cert_info()

        # Step 1: Validate certificate
        if not self._validate_cert(cert, domain_or_instance):
            raise CertValidationError(
                f"Certificate validation failed: domain {domain_or_instance} "
                f"is not in the certificate or certificate has expired"
            )

        # Step 2: Compare certificate fingerprints (if force update is not required)
        if not self.config.force_update:
            current_fingerprint = self.get_current_cert_fingerprint()
            if current_fingerprint:
                new_fingerprint = self._calculate_fingerprint(cert)
                if new_fingerprint == current_fingerprint:
                    logger.info(
                        "Certificate unchanged, skipping renewal: %s, fingerprint=%s",
                        domain_or_instance,
                        new_fingerprint[:20] + "...",
                    )
                    return True
        else:
            logger.info(
                "Force update mode enabled, will update even if certificate "
                "is the same: %s",
                domain_or_instance,
            )

        # Step 3: Execute renewal
        return self._do_renew(cert, cert_private_key)

    @abstractmethod
    def _get_cert_info(self) -> tuple[str, str, str]:
        """
        Get certificate information
        :return: (cert, cert_private_key, domain_or_instance)
        """
        pass

    @abstractmethod
    def _validate_cert(self, cert: str, domain_or_instance: str) -> bool:
        """
        Validate certificate
        :param cert: Certificate content
        :param domain_or_instance: Domain name or instance ID
        :return: Whether valid
        """
        pass

    @abstractmethod
    def _calculate_fingerprint(self, cert: str) -> str:
        """
        Calculate certificate fingerprint
        :param cert: Certificate content
        :return: Certificate fingerprint
        """
        pass

    @abstractmethod
    def get_current_cert_fingerprint(self) -> str | None:
        """
        Get current certificate fingerprint
        :return: Certificate fingerprint, or None if query fails
        """
        pass

    @abstractmethod
    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """
        Execute certificate renewal (subclasses implement specific logic)
        :param cert: Certificate content
        :param cert_private_key: Certificate private key
        :return: Whether successful
        """
        pass
