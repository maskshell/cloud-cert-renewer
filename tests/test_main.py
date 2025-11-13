import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加父目录到路径，以便导入主模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import (
    CdnCertsRenewer,
    SlbCertsRenewer,
    ConfigError,
    CertValidationError,
    load_config,
)


class TestCdnCertsRenewer(unittest.TestCase):
    """CDN证书更新器测试"""

    def setUp(self):
        """测试前准备"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.domain_name = "test.example.com"
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        self.region = "cn-hangzhou"

    def test_create_client(self):
        """测试创建CDN客户端"""
        client = CdnCertsRenewer.create_client(
            self.access_key_id, self.access_key_secret
        )
        self.assertIsNotNone(client)
        self.assertEqual(client._config.access_key_id, self.access_key_id)
        self.assertEqual(client._config.access_key_secret, self.access_key_secret)

    @patch("main.is_cert_valid")
    @patch("main.CdnCertsRenewer.create_client")
    def test_renew_cert_success(self, mock_create_client, mock_is_cert_valid):
        """测试证书更新成功"""
        # 设置mock
        mock_is_cert_valid.return_value = True
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.set_cdn_domain_sslcertificate_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        # 执行测试
        result = CdnCertsRenewer.renew_cert(
            self.domain_name,
            self.cert,
            self.cert_private_key,
            self.region,
            self.access_key_id,
            self.access_key_secret,
        )

        # 验证结果
        self.assertTrue(result)
        mock_is_cert_valid.assert_called_once_with(self.cert, self.domain_name)
        mock_client.set_cdn_domain_sslcertificate_with_options.assert_called_once()

    @patch("main.is_cert_valid")
    def test_renew_cert_invalid_cert(self, mock_is_cert_valid):
        """测试证书验证失败"""
        # 设置mock
        mock_is_cert_valid.return_value = False

        # 执行测试并验证异常
        with self.assertRaises(CertValidationError):
            CdnCertsRenewer.renew_cert(
                self.domain_name,
                self.cert,
                self.cert_private_key,
                self.region,
                self.access_key_id,
                self.access_key_secret,
            )


class TestSlbCertsRenewer(unittest.TestCase):
    """SLB证书更新器测试"""

    def setUp(self):
        """测试前准备"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.instance_id = "test-instance-id"
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        self.region = "cn-hangzhou"

    def test_create_client(self):
        """测试创建SLB客户端"""
        client = SlbCertsRenewer.create_client(
            self.access_key_id, self.access_key_secret
        )
        self.assertIsNotNone(client)
        self.assertEqual(client._config.access_key_id, self.access_key_id)
        self.assertEqual(client._config.access_key_secret, self.access_key_secret)

    @patch("main.SlbCertsRenewer.create_client")
    def test_renew_cert_success(self, mock_create_client):
        """测试证书更新成功"""
        # 设置mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = mock_response
        mock_create_client.return_value = mock_client

        # 执行测试
        result = SlbCertsRenewer.renew_cert(
            self.instance_id,
            self.cert,
            self.cert_private_key,
            self.region,
            self.access_key_id,
            self.access_key_secret,
        )

        # 验证结果
        self.assertTrue(result)
        mock_client.upload_server_certificate_with_options.assert_called_once()


class TestLoadConfig(unittest.TestCase):
    """配置加载测试"""

    def setUp(self):
        """测试前准备"""
        # 清除环境变量
        self.original_env = os.environ.copy()

    def tearDown(self):
        """测试后清理"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_config_cdn(self):
        """测试加载CDN配置"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "test_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        result = load_config()
        self.assertEqual(result[0], "cdn")
        self.assertEqual(result[1], "test_key_id")
        self.assertEqual(result[2], "test_key_secret")
        self.assertEqual(result[3], "test.example.com")
        self.assertEqual(result[4], "test_cert")
        self.assertEqual(result[5], "test_key")
        self.assertEqual(result[6], "cn-hangzhou")

    def test_load_config_slb(self):
        """测试加载SLB配置"""
        os.environ.update(
            {
                "SERVICE_TYPE": "slb",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "test_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "SLB_INSTANCE_ID": "test-instance-id",
                "SLB_CERT": "test_cert",
                "SLB_CERT_PRIVATE_KEY": "test_key",
                "SLB_REGION": "cn-beijing",
            }
        )

        result = load_config()
        self.assertEqual(result[0], "slb")
        self.assertEqual(result[1], "test_key_id")
        self.assertEqual(result[2], "test_key_secret")
        self.assertEqual(result[3], "test-instance-id")
        self.assertEqual(result[4], "test_cert")
        self.assertEqual(result[5], "test_key")
        self.assertEqual(result[6], "cn-beijing")

    def test_load_config_missing_access_key(self):
        """测试缺少访问凭证"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CDN_DOMAIN_NAME": "test.example.com",
            }
        )

        with self.assertRaises(ConfigError):
            load_config()

    def test_load_config_missing_domain_name(self):
        """测试缺少域名"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "test_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
            }
        )

        with self.assertRaises(ConfigError):
            load_config()

    def test_load_config_invalid_service_type(self):
        """测试无效的服务类型"""
        os.environ.update(
            {
                "SERVICE_TYPE": "invalid",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "test_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
            }
        )

        with self.assertRaises(ConfigError):
            load_config()


if __name__ == "__main__":
    unittest.main()
