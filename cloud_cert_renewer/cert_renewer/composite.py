"""Composite certificate renewer

Implements composite pattern for handling multiple resources.
"""

import logging

from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer

logger = logging.getLogger(__name__)


class CompositeCertRenewer:
    """Composite certificate renewer"""

    def __init__(self, renewers: list[BaseCertRenewer]) -> None:
        """
        Initialize composite renewer
        :param renewers: List of certificate renewers
        """
        self.renewers = renewers

    def renew(self) -> bool:
        """
        Renew all certificates
        Executes renewal for all managed resources using "best effort" strategy.
        If any renewal fails, logs the error and continues with others.
        :return: True if ALL renewals succeeded, False if ANY failed
        """
        if not self.renewers:
            logger.warning("No resources to renew")
            return True

        failures = 0
        total = len(self.renewers)

        logger.info("Starting batch renewal for %d resources...", total)

        for i, renewer in enumerate(self.renewers, 1):
            try:
                # We can't easily get the target name here without modifying base class,
                # but the renewer itself logs detailed info.
                logger.info("[%d/%d] Processing resource...", i, total)
                if not renewer.renew():
                    failures += 1
            except Exception as e:
                logger.exception(
                    "[%d/%d] Unexpected error during renewal: %s", i, total, e
                )
                failures += 1

        if failures > 0:
            logger.error(
                "Batch renewal completed with errors: %d/%d failed", failures, total
            )
            return False

        logger.info(
            "Batch renewal completed successfully: %d/%d succeeded", total, total
        )
        return True
