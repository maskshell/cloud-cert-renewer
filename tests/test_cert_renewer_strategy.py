"""Tests for certificate renewer strategies (Strategy Pattern)

Tests the Strategy Pattern implementation for certificate renewal.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.base import CertValidationError  # noqa: E402
from cloud_cert_renewer.cert_renewer.cdn_renewer import (  # noqa: E402
    CdnCertRenewerStrategy,
)
from cloud_cert_renewer.cert_renewer.load_balancer_renewer import (  # noqa: E402
    LoadBalancerCertRenewerStrategy,
)
from cloud_cert_renewer.config.models import (  # noqa: E402
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
)


class TestCdnCertRenewerStrategy(unittest.TestCase):
    """CDN certificate renewer strategy tests (Strategy Pattern)"""

    def setUp(self):
        """Test setup"""
        self.credentials = Credentials(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )
        self.config = AppConfig(
            service_type="cdn",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            cdn_config=CdnConfig(
                domain_name="test.example.com",
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
            ),
        )
        self.strategy = CdnCertRenewerStrategy(self.config)

    def test_get_cert_info_missing_config(self):
        """Test get_cert_info raises error when cdn_config is missing"""
        # Create a strategy and manually set config.cdn_config to None to test the error
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.cdn_config = None
        strategy = CdnCertRenewerStrategy(mock_config)

        with self.assertRaises(ValueError) as context:
            strategy._get_cert_info()

        self.assertIn("CDN configuration does not exist", str(context.exception))

    def test_get_cert_info(self):
        """Test getting certificate information"""
        cert, cert_key, domain = self.strategy._get_cert_info()

        self.assertEqual(cert, "test_cert")
        self.assertEqual(cert_key, "test_key")
        self.assertEqual(domain, "test.example.com")

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    def test_validate_cert(self, mock_is_cert_valid):
        """Test certificate validation"""
        mock_is_cert_valid.return_value = True

        result = self.strategy._validate_cert("test_cert", "test.example.com")

        self.assertTrue(result)
        mock_is_cert_valid.assert_called_once_with("test_cert", "test.example.com")

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.get_cert_fingerprint_sha256")
    def test_calculate_fingerprint(self, mock_get_fingerprint):
        """Test fingerprint calculation"""
        mock_get_fingerprint.return_value = "test:fingerprint:sha256"

        result = self.strategy._calculate_fingerprint("test_cert")

        self.assertEqual(result, "test:fingerprint:sha256")
        mock_get_fingerprint.assert_called_once_with("test_cert")

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.get_cert_fingerprint_sha256")
    def test_get_current_cert_fingerprint(self, mock_get_fingerprint, mock_get_cert):
        """Test getting current certificate fingerprint"""
        mock_get_cert.return_value = "current_cert_content"
        mock_get_fingerprint.return_value = "current:fingerprint"

        result = self.strategy.get_current_cert_fingerprint()

        self.assertEqual(result, "current:fingerprint")
        mock_get_cert.assert_called_once()
        mock_get_fingerprint.assert_called_once_with("current_cert_content")

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.renew_cert")
    def test_do_renew(self, mock_renew_cert):
        """Test executing certificate renewal"""
        mock_renew_cert.return_value = True

        result = self.strategy._do_renew("test_cert", "test_key")

        self.assertTrue(result)
        mock_renew_cert.assert_called_once()

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy.get_current_cert_fingerprint"
    )
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.get_cert_fingerprint_sha256")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.renew_cert")
    def test_strategy_renew_success(
        self,
        mock_renew_cert,
        mock_get_fingerprint,
        mock_get_current_fingerprint,
        mock_is_cert_valid,
    ):
        """Test successful certificate renewal through strategy"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_fingerprint.return_value = None  # No current certificate
        mock_get_fingerprint.return_value = "new:fingerprint"
        mock_renew_cert.return_value = True

        result = self.strategy.renew()

        self.assertTrue(result)
        mock_is_cert_valid.assert_called_once()
        mock_renew_cert.assert_called_once()

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.get_cert_fingerprint_sha256")
    def test_strategy_renew_skip_when_same(
        self, mock_get_fingerprint, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test strategy skips renewal when certificate is the same"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = "current_cert"
        mock_get_fingerprint.return_value = "same:fingerprint"  # Same fingerprint

        result = self.strategy.renew()

        self.assertTrue(result)
        # Verify renewal was skipped (renew_cert should not be called)
        # This is verified by the fact that we don't patch renew_cert

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    def test_strategy_renew_invalid_cert(self, mock_is_cert_valid):
        """Test strategy raises error for invalid certificate"""
        mock_is_cert_valid.return_value = False

        with self.assertRaises(CertValidationError):
            self.strategy.renew()


class TestLoadBalancerCertRenewerStrategy(unittest.TestCase):
    """Load Balancer certificate renewer strategy tests (Strategy Pattern)"""

    def setUp(self):
        """Test setup"""
        self.credentials = Credentials(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )
        self.config = AppConfig(
            service_type="lb",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            lb_config=LoadBalancerConfig(
                instance_id="test-instance-id",
                listener_port=443,
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
            ),
        )
        self.strategy = LoadBalancerCertRenewerStrategy(self.config)

    def test_get_cert_info(self):
        """Test getting certificate information"""
        cert, cert_key, instance_id = self.strategy._get_cert_info()

        self.assertEqual(cert, "test_cert")
        self.assertEqual(cert_key, "test_key")
        self.assertEqual(instance_id, "test-instance-id")

    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.x509.load_pem_x509_certificate"
    )
    def test_validate_cert(self, mock_load_cert):
        """Test certificate validation"""
        mock_load_cert.return_value = MagicMock()

        result = self.strategy._validate_cert("test_cert", "test-instance-id")

        self.assertTrue(result)
        mock_load_cert.assert_called_once()

    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.get_cert_fingerprint_sha1"
    )
    def test_calculate_fingerprint(self, mock_get_fingerprint):
        """Test fingerprint calculation"""
        mock_get_fingerprint.return_value = "test:fingerprint:sha1"

        result = self.strategy._calculate_fingerprint("test_cert")

        self.assertEqual(result, "test:fingerprint:sha1")
        mock_get_fingerprint.assert_called_once_with("test_cert")

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint"
    )
    def test_get_current_cert_fingerprint(self, mock_get_fingerprint):
        """Test getting current certificate fingerprint"""
        mock_get_fingerprint.return_value = "current:fingerprint"

        result = self.strategy.get_current_cert_fingerprint()

        self.assertEqual(result, "current:fingerprint")
        mock_get_fingerprint.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.renew_cert")
    def test_do_renew(self, mock_renew_cert):
        """Test executing certificate renewal"""
        mock_renew_cert.return_value = True

        result = self.strategy._do_renew("test_cert", "test_key")

        self.assertTrue(result)
        mock_renew_cert.assert_called_once()

    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.x509.load_pem_x509_certificate"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.LoadBalancerCertRenewerStrategy.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.get_cert_fingerprint_sha1"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.renew_cert")
    def test_strategy_renew_success(
        self,
        mock_renew_cert,
        mock_get_fingerprint,
        mock_get_current_fingerprint,
        mock_load_cert,
    ):
        """Test successful certificate renewal through strategy"""
        # Setup mocks
        mock_load_cert.return_value = MagicMock()
        mock_get_current_fingerprint.return_value = None  # No current certificate
        mock_get_fingerprint.return_value = "new:fingerprint"
        mock_renew_cert.return_value = True

        result = self.strategy.renew()

        self.assertTrue(result)
        mock_renew_cert.assert_called_once()

    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.x509.load_pem_x509_certificate"
    )
    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.get_cert_fingerprint_sha1"
    )
    def test_strategy_renew_skip_when_same(
        self, mock_get_fingerprint, mock_get_current_fingerprint, mock_load_cert
    ):
        """Test strategy skips renewal when certificate is the same"""
        # Setup mocks
        mock_load_cert.return_value = MagicMock()
        mock_get_current_fingerprint.return_value = "same:fingerprint"
        mock_get_fingerprint.return_value = "same:fingerprint"  # Same fingerprint

        result = self.strategy.renew()

        self.assertTrue(result)
        # Verify renewal was skipped

    def test_get_cert_info_missing_config(self):
        """Test get_cert_info raises error when lb_config is missing"""
        # Create a strategy and manually set config.lb_config to None to test the error
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.lb_config = None
        strategy = LoadBalancerCertRenewerStrategy(mock_config)

        with self.assertRaises(ValueError) as context:
            strategy._get_cert_info()

        self.assertIn(
            "Load Balancer configuration does not exist", str(context.exception)
        )

    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.x509.load_pem_x509_certificate"
    )
    def test_validate_cert_invalid_format(self, mock_load_cert):
        """Test certificate validation with invalid format"""

        # Mock to raise exception for invalid certificate
        mock_load_cert.side_effect = ValueError("Invalid certificate format")

        result = self.strategy._validate_cert("invalid_cert", "test-instance-id")

        self.assertFalse(result)

    def test_get_current_cert_fingerprint_missing_config(self):
        """Test get_current_cert_fingerprint returns None when lb_config is missing"""
        # Create a strategy and manually set config.lb_config to None to test
        # the early return
        # We can't create AppConfig with None lb_config due to validation,
        # so we test differently by creating a mock config object
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.lb_config = None
        strategy = LoadBalancerCertRenewerStrategy(mock_config)

        result = strategy.get_current_cert_fingerprint()

        self.assertIsNone(result)

    def test_do_renew_missing_config(self):
        """Test _do_renew raises error when lb_config is missing"""
        # Create a strategy and manually set config.lb_config to None to test the error
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_config.lb_config = None
        strategy = LoadBalancerCertRenewerStrategy(mock_config)

        with self.assertRaises(ValueError) as context:
            strategy._do_renew("test_cert", "test_key")

        self.assertIn(
            "Load Balancer configuration does not exist", str(context.exception)
        )


if __name__ == "__main__":
    unittest.main()
