import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.utils.ssl_cert_parser import (  # noqa: I001
    get_cert_fingerprint_sha1,
    get_cert_fingerprint_sha256,
    is_cert_valid,
    is_domain_name_match,
    parse_cert_info,
)


class TestSslCertParser(unittest.TestCase):
    """Utility functions tests (SSL certificate parser)"""

    def setUp(self):
        """Test setup"""
        # Note: Test certificates are generated dynamically in individual tests
        # to ensure they are valid and can be parsed correctly

    def test_is_domain_name_match_exact(self):
        """Test exact domain name matching"""
        domain_list = ["test.example.com", "other.example.com"]
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertFalse(is_domain_name_match("unknown.example.com", domain_list))

    def test_is_domain_name_match_wildcard(self):
        """Test wildcard domain name matching"""
        domain_list = ["*.example.com"]
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertTrue(is_domain_name_match("sub.test.example.com", domain_list))
        self.assertFalse(is_domain_name_match("example.com", domain_list))
        self.assertFalse(is_domain_name_match("other.com", domain_list))

    def test_is_domain_name_match_mixed(self):
        """Test mixed domain name list matching"""
        domain_list = ["example.com", "*.example.com", "test.example.com"]
        self.assertTrue(is_domain_name_match("example.com", domain_list))
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertTrue(is_domain_name_match("sub.example.com", domain_list))
        self.assertFalse(is_domain_name_match("other.com", domain_list))

    def test_parse_cert_info(self):
        """Test parsing certificate information"""
        # Generate a simple test certificate using cryptography
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        # Create a simple self-signed certificate
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
                x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("test.example.com"),
                        x509.DNSName("*.example.com"),
                    ]
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM).decode(
            "utf-8"
        )

        domain_list, expire_date = parse_cert_info(cert_pem)

        self.assertIsInstance(domain_list, list)
        self.assertIsInstance(expire_date, str)
        # Expire date should be in format "YYYY-MM-DD HH:MM:SS"
        self.assertRegex(expire_date, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        # Should contain test.example.com from CN
        self.assertIn("test.example.com", domain_list)
        # Should also contain SAN domains
        self.assertIn("*.example.com", domain_list)

    def test_parse_cert_info_no_san_extension(self):
        """Test parsing certificate information without SAN extension"""
        # Generate a certificate without SAN extension
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM).decode(
            "utf-8"
        )

        domain_list, _ = parse_cert_info(cert_pem)

        self.assertIsInstance(domain_list, list)
        self.assertIn("test.example.com", domain_list)  # Should have CN

    @patch("cloud_cert_renewer.utils.ssl_cert_parser.parse_cert_info")
    @patch("cloud_cert_renewer.utils.ssl_cert_parser.is_domain_name_match")
    def test_is_cert_valid_with_valid_cert(self, mock_match, mock_parse):
        """Test valid certificate validation"""
        # Mock parse_cert_info to return valid cert info
        future_date = (datetime.now() + timedelta(days=30)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        mock_parse.return_value = (["test.example.com"], future_date)
        mock_match.return_value = True

        result = is_cert_valid("cert_content", "test.example.com")

        self.assertTrue(result)
        mock_parse.assert_called_once_with("cert_content")
        mock_match.assert_called_once()

    @patch("cloud_cert_renewer.utils.ssl_cert_parser.parse_cert_info")
    @patch("cloud_cert_renewer.utils.ssl_cert_parser.is_domain_name_match")
    def test_is_cert_valid_with_invalid_domain(self, mock_match, mock_parse):
        """Test certificate validation with mismatched domain"""
        future_date = (datetime.now() + timedelta(days=30)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        mock_parse.return_value = (["other.example.com"], future_date)
        mock_match.return_value = False

        result = is_cert_valid("cert_content", "test.example.com")

        self.assertFalse(result)

    @patch("cloud_cert_renewer.utils.ssl_cert_parser.parse_cert_info")
    @patch("cloud_cert_renewer.utils.ssl_cert_parser.is_domain_name_match")
    def test_is_cert_valid_with_expired_cert(self, mock_match, mock_parse):
        """Test expired certificate validation"""
        past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        mock_parse.return_value = (["test.example.com"], past_date)
        mock_match.return_value = True

        result = is_cert_valid("cert_content", "test.example.com")

        self.assertFalse(result)

    def _generate_test_certificate(self):
        """Generate a test certificate for testing"""
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        # Create a simple self-signed certificate
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
                x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("test.example.com"),
                        x509.DNSName("*.example.com"),
                    ]
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        return cert.public_bytes(encoding=serialization.Encoding.PEM).decode("utf-8")

    def test_get_cert_fingerprint_sha256(self):
        """Test SHA256 fingerprint calculation"""
        cert_content = self._generate_test_certificate()

        fingerprint = get_cert_fingerprint_sha256(cert_content)

        self.assertIsInstance(fingerprint, str)
        # SHA256 fingerprint should be 64 hex characters (32 bytes * 2)
        # in colon-separated format
        # Format: "XX:XX:XX:..." (64 hex chars = 32 pairs)
        parts = fingerprint.split(":")
        # 32 bytes = 32 colon-separated parts
        self.assertEqual(len(parts), 32)
        # Each part should be 2 hex characters
        for part in parts:
            self.assertEqual(len(part), 2)
            self.assertTrue(all(c in "0123456789ABCDEF" for c in part))

    def test_get_cert_fingerprint_sha1(self):
        """Test SHA1 fingerprint calculation"""
        cert_content = self._generate_test_certificate()

        fingerprint = get_cert_fingerprint_sha1(cert_content)

        self.assertIsInstance(fingerprint, str)
        # SHA1 fingerprint should be 40 hex characters (20 bytes * 2)
        # in colon-separated format
        # Format: "xx:xx:xx:..." (40 hex chars = 20 pairs)
        parts = fingerprint.split(":")
        # 20 bytes = 20 colon-separated parts
        self.assertEqual(len(parts), 20)
        # Each part should be 2 hex characters (lowercase)
        for part in parts:
            self.assertEqual(len(part), 2)
            self.assertTrue(all(c in "0123456789abcdef" for c in part))


if __name__ == "__main__":
    unittest.main()
