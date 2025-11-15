"""Tests for credential provider factory (Factory Pattern)

Tests the CredentialProviderFactory implementation of the Factory Pattern.
"""

import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider  # noqa: E402
from cloud_cert_renewer.auth.env import EnvCredentialProvider  # noqa: E402
from cloud_cert_renewer.auth.factory import CredentialProviderFactory  # noqa: E402
from cloud_cert_renewer.auth.iam_role import IAMRoleCredentialProvider  # noqa: E402
from cloud_cert_renewer.auth.service_account import (  # noqa: E402
    ServiceAccountCredentialProvider,
)
from cloud_cert_renewer.auth.sts import STSCredentialProvider  # noqa: E402
from cloud_cert_renewer.config.models import Credentials  # noqa: E402


class TestCredentialProviderFactory(unittest.TestCase):
    """Credential provider factory tests (Factory Pattern)"""

    def test_factory_create_access_key(self):
        """Test factory creates AccessKey credential provider"""
        provider = CredentialProviderFactory.create(
            auth_method="access_key",
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

        self.assertIsInstance(provider, AccessKeyCredentialProvider)
        credentials = provider.get_credentials()
        self.assertEqual(credentials.access_key_id, "test_key_id")
        self.assertEqual(credentials.access_key_secret, "test_key_secret")
        self.assertIsNone(credentials.security_token)

    def test_factory_create_access_key_with_credentials(self):
        """Test factory creates AccessKey provider from Credentials object"""
        credentials = Credentials(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

        provider = CredentialProviderFactory.create(
            auth_method="access_key", credentials=credentials
        )

        self.assertIsInstance(provider, AccessKeyCredentialProvider)

    def test_factory_create_sts(self):
        """Test factory creates STS credential provider"""
        provider = CredentialProviderFactory.create(
            auth_method="sts",
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_security_token",
        )

        self.assertIsInstance(provider, STSCredentialProvider)
        credentials = provider.get_credentials()
        self.assertEqual(credentials.access_key_id, "test_key_id")
        self.assertEqual(credentials.access_key_secret, "test_key_secret")
        self.assertEqual(credentials.security_token, "test_security_token")

    def test_factory_create_sts_with_credentials(self):
        """Test factory creates STS provider from Credentials object"""
        credentials = Credentials(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_security_token",
        )

        provider = CredentialProviderFactory.create(
            auth_method="sts", credentials=credentials
        )

        self.assertIsInstance(provider, STSCredentialProvider)

    def test_factory_create_env(self):
        """Test factory creates environment variable credential provider"""
        provider = CredentialProviderFactory.create(auth_method="env")

        self.assertIsInstance(provider, EnvCredentialProvider)

    def test_factory_invalid_auth_method(self):
        """Test factory raises error for invalid authentication method"""
        with self.assertRaises(ValueError) as context:
            CredentialProviderFactory.create(auth_method="invalid")

        self.assertIn("Unsupported authentication method", str(context.exception))

    def test_factory_access_key_missing_params(self):
        """Test factory raises error when access_key method missing parameters"""
        with self.assertRaises(ValueError) as context:
            CredentialProviderFactory.create(auth_method="access_key")

        self.assertIn(
            "requires access_key_id and access_key_secret", str(context.exception)
        )

    def test_factory_sts_missing_params(self):
        """Test factory raises error when sts method missing parameters"""
        with self.assertRaises(ValueError) as context:
            CredentialProviderFactory.create(
                auth_method="sts",
                access_key_id="test_key_id",
                access_key_secret="test_key_secret",
                # Missing security_token
            )

        self.assertIn(
            "requires access_key_id, access_key_secret and security_token",
            str(context.exception),
        )

    def test_factory_case_insensitive(self):
        """Test factory is case insensitive for auth method"""
        provider1 = CredentialProviderFactory.create(
            auth_method="ACCESS_KEY",
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )
        provider2 = CredentialProviderFactory.create(
            auth_method="access_key",
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

        self.assertIsInstance(provider1, AccessKeyCredentialProvider)
        self.assertIsInstance(provider2, AccessKeyCredentialProvider)

    def test_factory_create_iam_role(self):
        """Test factory creates IAM Role credential provider"""
        provider = CredentialProviderFactory.create(
            auth_method="iam_role",
            role_arn="arn:aws:iam::123456789012:role/test-role",
            role_session_name="test-session",
        )

        self.assertIsInstance(provider, IAMRoleCredentialProvider)

    def test_factory_create_iam_role_missing_role_arn(self):
        """Test factory raises error when iam_role method missing role_arn"""
        with self.assertRaises(ValueError) as context:
            CredentialProviderFactory.create(auth_method="iam_role")

        self.assertIn(
            "iam_role authentication method requires role_arn", str(context.exception)
        )

    def test_factory_create_iam_role_without_session_name(self):
        """Test factory creates IAM Role provider without session name"""
        provider = CredentialProviderFactory.create(
            auth_method="iam_role",
            role_arn="arn:aws:iam::123456789012:role/test-role",
        )

        self.assertIsInstance(provider, IAMRoleCredentialProvider)

    def test_factory_create_service_account(self):
        """Test factory creates ServiceAccount credential provider"""
        provider = CredentialProviderFactory.create(
            auth_method="service_account",
            service_account_path="/custom/path/to/serviceaccount",
        )

        self.assertIsInstance(provider, ServiceAccountCredentialProvider)

    def test_factory_create_service_account_default_path(self):
        """Test factory creates ServiceAccount provider with default path"""
        provider = CredentialProviderFactory.create(auth_method="service_account")

        self.assertIsInstance(provider, ServiceAccountCredentialProvider)


if __name__ == "__main__":
    unittest.main()
