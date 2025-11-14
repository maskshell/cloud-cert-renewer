"""Tests for certificate renewer factory (Factory Pattern)

Tests the CertRenewerFactory implementation of the Factory Pattern.
"""

import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.factory import CertRenewerFactory
from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.cert_renewer.cdn_renewer import CdnCertRenewerStrategy
from cloud_cert_renewer.cert_renewer.load_balancer_renewer import (
    LoadBalancerCertRenewerStrategy,
)
from cloud_cert_renewer.config.models import (
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
)


class TestCertRenewerFactory(unittest.TestCase):
    """Certificate renewer factory tests (Factory Pattern)"""

    def setUp(self):
        """Test setup"""
        self.credentials = Credentials(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

    def test_factory_create_cdn_renewer(self):
        """Test factory creates CDN renewer strategy"""
        config = AppConfig(
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

        renewer = CertRenewerFactory.create(config)

        self.assertIsInstance(renewer, BaseCertRenewer)
        self.assertIsInstance(renewer, CdnCertRenewerStrategy)
        self.assertEqual(renewer.config, config)

    def test_factory_create_lb_renewer(self):
        """Test factory creates Load Balancer renewer strategy"""
        config = AppConfig(
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

        renewer = CertRenewerFactory.create(config)

        self.assertIsInstance(renewer, BaseCertRenewer)
        self.assertIsInstance(renewer, LoadBalancerCertRenewerStrategy)
        self.assertEqual(renewer.config, config)

    def test_factory_invalid_service_type(self):
        """Test factory raises error for invalid service type"""
        config = AppConfig(
            service_type="invalid",
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

        with self.assertRaises(ValueError) as context:
            CertRenewerFactory.create(config)

        self.assertIn("Unsupported service type", str(context.exception))

    def test_factory_with_different_configs(self):
        """Test factory creates different renewers for different configs"""
        cdn_config = AppConfig(
            service_type="cdn",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            cdn_config=CdnConfig(
                domain_name="cdn.example.com",
                cert="cdn_cert",
                cert_private_key="cdn_key",
                region="cn-hangzhou",
            ),
        )

        lb_config = AppConfig(
            service_type="lb",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            lb_config=LoadBalancerConfig(
                instance_id="lb-instance-id",
                listener_port=443,
                cert="lb_cert",
                cert_private_key="lb_key",
                region="cn-beijing",
            ),
        )

        cdn_renewer = CertRenewerFactory.create(cdn_config)
        lb_renewer = CertRenewerFactory.create(lb_config)

        self.assertIsInstance(cdn_renewer, CdnCertRenewerStrategy)
        self.assertIsInstance(lb_renewer, LoadBalancerCertRenewerStrategy)
        self.assertNotEqual(type(cdn_renewer), type(lb_renewer))


if __name__ == "__main__":
    unittest.main()

