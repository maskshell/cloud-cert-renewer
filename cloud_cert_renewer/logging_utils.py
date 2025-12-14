from __future__ import annotations

import logging
import os


class RedactingFormatter(logging.Formatter):
    def __init__(self, fmt: str, datefmt: str | None = None) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)

        candidates = [
            os.environ.get("CLOUD_ACCESS_KEY_ID"),
            os.environ.get("CLOUD_ACCESS_KEY_SECRET"),
            os.environ.get("CLOUD_SECURITY_TOKEN"),
            os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            os.environ.get("ALIBABA_CLOUD_SECURITY_TOKEN"),
        ]
        self._secret_values = [v for v in candidates if v]

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        for value in self._secret_values:
            rendered = rendered.replace(value, "***REDACTED***")
        return rendered


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        RedactingFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root.handlers.clear()
    root.addHandler(handler)
