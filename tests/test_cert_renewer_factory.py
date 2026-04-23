"""Tests for certificate renewer factory (Factory Pattern)

Tests the CertRenewerFactory implementation of the Factory Pattern.
"""

import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.cdn_renewer import (  # noqa: E402
    CdnCertRenewerStrategy,
)
from cloud_cert_renewer.cert_renewer.composite import CompositeCertRenewer  # noqa: E402
from cloud_cert_renewer.cert_renewer.factory import CertRenewerFactory  # noqa: E402
from cloud_cert_renewer.cert_renewer.load_balancer_renewer import (  # noqa: E402
    LoadBalancerCertRenewerStrategy,
)
from cloud_cert_renewer.config.models import (  # noqa: E402
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
                domain_names=["test.example.com"],
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
            ),
        )

        renewer = CertRenewerFactory.create(config)

        self.assertIsInstance(renewer, CompositeCertRenewer)
        self.assertEqual(len(renewer.renewers), 1)
        self.assertIsInstance(renewer.renewers[0], CdnCertRenewerStrategy)
        self.assertEqual(renewer.renewers[0].config, config)

    def test_factory_create_lb_renewer(self):
        """Test factory creates Load Balancer renewer strategy"""
        config = AppConfig(
            service_type="lb",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            lb_config=LoadBalancerConfig(
                instance_ids=["test-instance-id"],
                listener_port=443,
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
            ),
        )

        renewer = CertRenewerFactory.create(config)

        self.assertIsInstance(renewer, CompositeCertRenewer)
        self.assertEqual(len(renewer.renewers), 1)
        self.assertIsInstance(renewer.renewers[0], LoadBalancerCertRenewerStrategy)
        self.assertEqual(renewer.renewers[0].config, config)

    def test_factory_invalid_service_type(self):
        """Test factory raises error for invalid service type"""
        config = AppConfig(
            service_type="invalid",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            cdn_config=CdnConfig(
                domain_names=["test.example.com"],
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
                domain_names=["cdn.example.com"],
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
                instance_ids=["lb-instance-id"],
                listener_port=443,
                cert="lb_cert",
                cert_private_key="lb_key",
                region="cn-beijing",
            ),
        )

        cdn_renewer = CertRenewerFactory.create(cdn_config)
        lb_renewer = CertRenewerFactory.create(lb_config)

        self.assertIsInstance(cdn_renewer, CompositeCertRenewer)
        self.assertIsInstance(cdn_renewer.renewers[0], CdnCertRenewerStrategy)

        self.assertIsInstance(lb_renewer, CompositeCertRenewer)
        self.assertIsInstance(lb_renewer.renewers[0], LoadBalancerCertRenewerStrategy)

        self.assertNotEqual(type(cdn_renewer.renewers[0]), type(lb_renewer.renewers[0]))

    def test_factory_create_lb_renewer_with_listeners(self):
        """Test factory creates separate strategies for each listener pair"""
        config = AppConfig(
            service_type="lb",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            lb_config=LoadBalancerConfig(
                instance_ids=[],  # empty, using listeners instead
                listener_port=0,  # not used
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
                listeners=[("lb-aaa", 443), ("lb-bbb", 8443)],
            ),
        )
        renewer = CertRenewerFactory.create(config)
        self.assertEqual(len(renewer.renewers), 2)
        self.assertEqual(renewer.renewers[0].target_instance_id, "lb-aaa")
        self.assertEqual(renewer.renewers[0].target_listener_port, 443)
        self.assertEqual(renewer.renewers[1].target_instance_id, "lb-bbb")
        self.assertEqual(renewer.renewers[1].target_listener_port, 8443)

    def test_factory_lb_listeners_takes_precedence_over_instance_ids(self):
        """Test listeners field takes precedence over instance_ids"""
        config = AppConfig(
            service_type="lb",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=self.credentials,
            force_update=False,
            lb_config=LoadBalancerConfig(
                instance_ids=["lb-old-1", "lb-old-2"],
                listener_port=443,
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
                listeners=[("lb-new", 8443)],
            ),
        )
        renewer = CertRenewerFactory.create(config)
        # Should only create 1 renewer from listeners, not 2 from instance_ids
        self.assertEqual(len(renewer.renewers), 1)
        self.assertEqual(renewer.renewers[0].target_instance_id, "lb-new")
        self.assertEqual(renewer.renewers[0].target_listener_port, 8443)


if __name__ == "__main__":
    unittest.main()
