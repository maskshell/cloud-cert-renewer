"""Tests for certificate renewer base class (Template Method Pattern)

Tests the Template Method Pattern implementation in BaseCertRenewer.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.base import (  # noqa: E402
    BaseCertRenewer,
    CertValidationError,
)
from cloud_cert_renewer.config.models import (  # noqa: E402
    AppConfig,
    CdnConfig,
    Credentials,
)


class MockCertRenewer(BaseCertRenewer):
    """Mock certificate renewer for testing Template Method Pattern"""

    def _get_cert_info(self) -> tuple[str, str, str]:
        """Get certificate information"""
        return ("test_cert", "test_key", "test.example.com")

    def _validate_cert(self, cert: str, domain_or_instance: str) -> bool:
        """Validate certificate"""
        return self._mock_validate_cert(cert, domain_or_instance)

    def _calculate_fingerprint(self, cert: str) -> str:
        """Calculate fingerprint"""
        return self._mock_calculate_fingerprint(cert)

    def get_current_cert_fingerprint(self) -> str | None:
        """Get current fingerprint"""
        return self._mock_get_current_fingerprint()

    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """Execute renewal"""
        return self._mock_do_renew(cert, cert_private_key)

    def __init__(self, config: AppConfig) -> None:
        """Initialize with mocks"""
        super().__init__(config)
        self._mock_validate_cert = MagicMock(return_value=True)
        self._mock_calculate_fingerprint = MagicMock(return_value="test:fingerprint")
        self._mock_get_current_fingerprint = MagicMock(return_value=None)
        self._mock_do_renew = MagicMock(return_value=True)


class TestBaseCertRenewer(unittest.TestCase):
    """Base certificate renewer tests (Template Method Pattern)"""

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
                domain_names=["test.example.com"],
                cert="test_cert",
                cert_private_key="test_key",
                region="cn-hangzhou",
            ),
        )
        self.renewer = MockCertRenewer(self.config)

    def test_template_method_renew_flow(self):
        """Test template method renew() complete flow"""
        result = self.renewer.renew()

        # Verify template method flow
        self.assertTrue(result)
        self.renewer._mock_validate_cert.assert_called_once_with(
            "test_cert", "test.example.com"
        )
        self.renewer._mock_get_current_fingerprint.assert_called_once()
        self.renewer._mock_do_renew.assert_called_once_with("test_cert", "test_key")

    def test_template_method_validation_step(self):
        """Test template method validation step"""
        # Setup mock to fail validation
        self.renewer._mock_validate_cert.return_value = False

        with self.assertRaises(CertValidationError):
            self.renewer.renew()

        # Verify validation was called
        self.renewer._mock_validate_cert.assert_called_once()
        # Verify renewal was not executed
        self.renewer._mock_do_renew.assert_not_called()

    def test_template_method_fingerprint_comparison(self):
        """Test template method fingerprint comparison step"""
        # Setup mock to return same fingerprint
        self.renewer._mock_get_current_fingerprint.return_value = "test:fingerprint"
        self.renewer._mock_calculate_fingerprint.return_value = "test:fingerprint"

        result = self.renewer.renew()

        # Verify renewal was skipped (do_renew not called)
        self.assertTrue(result)
        self.renewer._mock_do_renew.assert_not_called()

    def test_template_method_force_update(self):
        """Test template method with force update enabled"""
        # Setup config with force_update=True
        self.config.force_update = True
        self.renewer = MockCertRenewer(self.config)
        self.renewer._mock_get_current_fingerprint.return_value = "same:fingerprint"
        self.renewer._mock_calculate_fingerprint.return_value = "same:fingerprint"

        result = self.renewer.renew()

        # Verify renewal was executed even with same fingerprint
        self.assertTrue(result)
        self.renewer._mock_do_renew.assert_called_once()

    def test_template_method_skip_when_same(self):
        """Test template method skips renewal when certificate is the same"""
        # Setup mocks
        self.renewer._mock_get_current_fingerprint.return_value = "same:fingerprint"
        self.renewer._mock_calculate_fingerprint.return_value = "same:fingerprint"

        result = self.renewer.renew()

        # Verify renewal was skipped
        self.assertTrue(result)
        self.renewer._mock_do_renew.assert_not_called()

    def test_template_method_no_current_cert(self):
        """Test template method when no current certificate exists"""
        # Setup mock to return None (no current certificate)
        self.renewer._mock_get_current_fingerprint.return_value = None

        result = self.renewer.renew()

        # Verify renewal was executed
        self.assertTrue(result)
        self.renewer._mock_do_renew.assert_called_once()

    def test_template_method_abstract_methods(self):
        """Test that abstract methods must be implemented"""
        # Try to instantiate BaseCertRenewer directly (should fail)
        with self.assertRaises(TypeError):
            BaseCertRenewer(self.config)  # type: ignore

    def test_template_method_dry_run(self):
        """Test template method with dry_run enabled"""
        # Setup config with dry_run=True
        self.config.dry_run = True
        self.renewer = MockCertRenewer(self.config)

        # Ensure validation passes
        self.renewer._mock_validate_cert.return_value = True
        # Ensure fingerprints differ so it would normally update
        self.renewer._mock_get_current_fingerprint.return_value = "old:fingerprint"
        self.renewer._mock_calculate_fingerprint.return_value = "new:fingerprint"

        result = self.renewer.renew()

        # Verify validation was called
        self.renewer._mock_validate_cert.assert_called_once()
        # Verify fingerprint logic ran
        self.renewer._mock_get_current_fingerprint.assert_called_once()
        # Verify do_renew was NOT called
        self.renewer._mock_do_renew.assert_not_called()
        # Verify it returns True
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
