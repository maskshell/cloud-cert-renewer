"""CLI smoke tests.

Validates the full flow:
env config -> DI container -> renewer factory -> adapter factory -> auth provider.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cli import run  # noqa: E402
from cloud_cert_renewer.container import get_container  # noqa: E402


def _generate_self_signed_cert() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SmokeTest"),
            x509.NameAttribute(NameOID.COMMON_NAME, "example.com"),
        ]
    )

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("example.com")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    return cert_pem, key_pem


class TestCliSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = os.environ.copy()
        get_container().clear()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        get_container().clear()

    @patch("cloud_cert_renewer.providers.noop.CredentialProviderFactory.create")
    def test_cli_smoke_lb_noop(self, mock_create: MagicMock) -> None:
        mock_provider = MagicMock()
        mock_provider.get_credential_client.return_value = MagicMock()
        mock_create.return_value = mock_provider

        cert_pem, key_pem = _generate_self_signed_cert()

        os.environ.update(
            {
                "SERVICE_TYPE": "lb",
                "CLOUD_PROVIDER": "noop",
                "AUTH_METHOD": "access_key",
                "CLOUD_ACCESS_KEY_ID": "dummy_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "dummy_key_secret",
                "LB_INSTANCE_ID": "smoke-instance",
                "LB_LISTENER_PORT": "443",
                "LB_REGION": "cn-hangzhou",
                "LB_CERT": cert_pem,
                "LB_CERT_PRIVATE_KEY": key_pem,
            }
        )

        code = run()
        self.assertEqual(code, 0)

        self.assertGreaterEqual(mock_create.call_count, 1)
