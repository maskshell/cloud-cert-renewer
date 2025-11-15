"""Tests for credential providers (Strategy Pattern)

Tests the various credential provider implementations (Strategy Pattern).
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider
from cloud_cert_renewer.auth.sts import STSCredentialProvider
from cloud_cert_renewer.auth.env import EnvCredentialProvider
from cloud_cert_renewer.config.models import Credentials


class TestAccessKeyCredentialProvider(unittest.TestCase):
    """AccessKey credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.provider = AccessKeyCredentialProvider(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

    def test_get_credentials(self):
        """Test getting credentials"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "test_key_id")
        self.assertEqual(credentials.access_key_secret, "test_key_secret")
        self.assertIsNone(credentials.security_token)


class TestSTSCredentialProvider(unittest.TestCase):
    """STS credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.provider = STSCredentialProvider(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_security_token",
        )

    def test_get_credentials(self):
        """Test getting credentials"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "test_key_id")
        self.assertEqual(credentials.access_key_secret, "test_key_secret")
        self.assertEqual(credentials.security_token, "test_security_token")


class TestEnvCredentialProvider(unittest.TestCase):
    """Environment variable credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.provider = EnvCredentialProvider()
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Test cleanup"""
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch.dict(
        os.environ,
        {
            "CLOUD_ACCESS_KEY_ID": "env_key_id",
            "CLOUD_ACCESS_KEY_SECRET": "env_key_secret",
        },
    )
    def test_get_credentials_from_env(self):
        """Test getting credentials from environment variables"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "env_key_id")
        self.assertEqual(credentials.access_key_secret, "env_key_secret")

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ACCESS_KEY_ID": "legacy_key_id",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "legacy_key_secret",
        },
    )
    def test_get_credentials_from_legacy_env(self):
        """Test getting credentials from legacy environment variables"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "legacy_key_id")
        self.assertEqual(credentials.access_key_secret, "legacy_key_secret")

    @patch.dict(
        os.environ,
        {
            "CLOUD_ACCESS_KEY_ID": "new_key_id",
            "CLOUD_ACCESS_KEY_SECRET": "new_key_secret",
            "ALIBABA_CLOUD_ACCESS_KEY_ID": "legacy_key_id",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "legacy_key_secret",
        },
    )
    def test_get_credentials_prioritizes_new_env(self):
        """Test that new environment variables take priority over legacy ones"""
        credentials = self.provider.get_credentials()

        self.assertEqual(credentials.access_key_id, "new_key_id")
        self.assertEqual(credentials.access_key_secret, "new_key_secret")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_credentials_missing_env(self):
        """Test getting credentials when environment variables are missing"""
        with self.assertRaises(ValueError) as context:
            self.provider.get_credentials()

        self.assertIn("Missing required environment variables", str(context.exception))


if __name__ == "__main__":
    unittest.main()
