from __future__ import annotations

import logging

from cloud_cert_renewer.cert_renewer import (
    CertRenewerFactory,
    CertValidationError,
)
from cloud_cert_renewer.config import ConfigError, load_config
from cloud_cert_renewer.container import get_container, register_service


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


logger = logging.getLogger(__name__)


def run() -> int:
    _configure_logging()

    try:
        config = load_config()

        container = get_container()
        register_service("config", instance=config, singleton=True)
        register_service(
            "cert_renewer_factory",
            instance=CertRenewerFactory,
            singleton=True,
        )

        logger.info(
            "Starting certificate renewal: service_type=%s, cloud_provider=%s, "
            "auth_method=%s",
            config.service_type,
            config.cloud_provider,
            config.auth_method,
        )

        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)
        success = renewer.renew()

        if success:
            logger.info("Certificate renewal completed")
            return 0

        logger.error("Certificate renewal failed")
        return 1

    except ConfigError as e:
        logger.error("Configuration error: %s", e)
        return 1
    except CertValidationError as e:
        logger.error("Certificate validation error: %s", e)
        return 1
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error occurred: %s", e)
        return 1


def main() -> None:
    raise SystemExit(run())
