"""Integration tests

Tests the complete integration flow from configuration loading to certificate renewal.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer import (  # noqa: E402
    CertRenewerFactory,
    CertValidationError,
)
from cloud_cert_renewer.config import ConfigError, load_config  # noqa: E402
from cloud_cert_renewer.container import get_container, register_service  # noqa: E402


class TestIntegration(unittest.TestCase):
    """Integration tests for complete certificate renewal flow"""

    def setUp(self):
        """Test setup"""
        self.original_env = os.environ.copy()
        # Clear global container
        container = get_container()
        container.clear()

    def tearDown(self):
        """Test cleanup"""
        os.environ.clear()
        os.environ.update(self.original_env)
        container = get_container()
        container.clear()

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.renew_cert")
    def test_main_cdn_renewal_flow(
        self, mock_renew_cert, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test complete CDN certificate renewal flow"""
        # Setup environment
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = None
        mock_renew_cert.return_value = True

        # Load configuration
        config = load_config()

        # Register to container
        container = get_container()
        register_service("config", instance=config, singleton=True)
        register_service(
            "cert_renewer_factory", instance=CertRenewerFactory, singleton=True
        )

        # Get factory and create renewer
        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)

        # Execute renewal
        result = renewer.renew()

        # Verify results
        self.assertTrue(result)
        mock_is_cert_valid.assert_called_once()
        mock_renew_cert.assert_called_once()

    @patch(
        "cloud_cert_renewer.cert_renewer.load_balancer_renewer.x509.load_pem_x509_certificate"
    )
    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.renew_cert")
    def test_main_lb_renewal_flow(
        self, mock_renew_cert, mock_get_fingerprint, mock_load_cert
    ):
        """Test complete Load Balancer certificate renewal flow"""
        # Setup environment
        os.environ.update(
            {
                "SERVICE_TYPE": "lb",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "LB_INSTANCE_ID": "test-instance-id",
                "LB_LISTENER_PORT": "443",
                "LB_CERT": "test_cert",
                "LB_CERT_PRIVATE_KEY": "test_key",
                "LB_REGION": "cn-hangzhou",
            }
        )

        # Setup mocks
        mock_load_cert.return_value = MagicMock()
        mock_get_fingerprint.return_value = None
        mock_renew_cert.return_value = True

        # Load configuration
        config = load_config()

        # Register to container
        container = get_container()
        register_service("config", instance=config, singleton=True)
        register_service(
            "cert_renewer_factory", instance=CertRenewerFactory, singleton=True
        )

        # Get factory and create renewer
        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)

        # Execute renewal
        result = renewer.renew()

        # Verify results
        self.assertTrue(result)
        mock_renew_cert.assert_called_once()

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    def test_main_error_handling(self, mock_is_cert_valid):
        """Test error handling in complete flow"""
        # Setup environment
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        # Setup mock to fail validation
        mock_is_cert_valid.return_value = False

        # Load configuration
        config = load_config()

        # Register to container
        container = get_container()
        register_service("config", instance=config, singleton=True)
        register_service(
            "cert_renewer_factory", instance=CertRenewerFactory, singleton=True
        )

        # Get factory and create renewer
        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)

        # Execute renewal and verify exception
        with self.assertRaises(CertValidationError):
            renewer.renew()

    def test_integration_config_loading_error(self):
        """Test integration with configuration loading error"""
        # Setup environment with missing required variables
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                # Missing CLOUD_ACCESS_KEY_ID and CLOUD_ACCESS_KEY_SECRET
            }
        )

        # Verify configuration loading fails
        with self.assertRaises(ConfigError):
            load_config()

    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy.get_current_cert_fingerprint"
    )
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.get_cert_fingerprint_sha256")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.renew_cert")
    def test_integration_with_dependency_injection(
        self,
        mock_renew_cert,
        mock_get_fingerprint,
        mock_get_current_fingerprint,
        mock_is_cert_valid,
    ):
        """Test integration with dependency injection container"""
        # Setup environment
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_fingerprint.return_value = (
            "current:fingerprint"  # Current certificate fingerprint
        )
        mock_get_fingerprint.return_value = (
            "different:fingerprint"  # New certificate fingerprint (different)
        )
        mock_renew_cert.return_value = True

        # Load configuration
        config = load_config()

        # Register services to container
        container = get_container()
        register_service("config", instance=config, singleton=True)
        register_service(
            "cert_renewer_factory", instance=CertRenewerFactory, singleton=True
        )

        # Get services from container
        factory = container.get("cert_renewer_factory")
        renewer = factory.create(container.get("config"))

        # Execute renewal
        result = renewer.renew()

        # Verify results
        self.assertTrue(result)
        mock_renew_cert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
