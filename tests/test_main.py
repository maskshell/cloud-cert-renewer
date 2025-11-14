import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_slb20140515.client import Client as Slb20140515Client

# 添加父目录到路径，以便导入主模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import (  # noqa: I001
    CdnCertsRenewer,
    CertValidationError,
    ConfigError,
    SlbCertsRenewer,
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
        # 验证客户端类型
        self.assertIsInstance(client, Cdn20180510Client)

    @patch("main.is_cert_valid")
    @patch("main.CdnCertsRenewer.get_current_cert")
    @patch("main.CdnCertsRenewer.create_client")
    def test_renew_cert_success(
        self, mock_create_client, mock_get_current_cert, mock_is_cert_valid
    ):
        """测试证书更新成功"""
        # 设置mock
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = None  # 没有当前证书，需要更新
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
        mock_get_current_cert.assert_called_once_with(
            self.domain_name, self.access_key_id, self.access_key_secret
        )
        mock_client.set_cdn_domain_sslcertificate_with_options.assert_called_once()

    @patch("main.is_cert_valid")
    @patch("main.CdnCertsRenewer.get_current_cert")
    @patch("main.get_cert_fingerprint_sha256")
    def test_renew_cert_skip_when_same(
        self, mock_get_fingerprint, mock_get_current_cert, mock_is_cert_valid
    ):
        """测试证书相同时跳过更新"""
        # 设置mock
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = "current_cert_content"
        mock_get_fingerprint.return_value = "SAME:FINGERPRINT:VALUE"

        # 执行测试（默认 force=False）
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
        mock_get_current_cert.assert_called_once_with(
            self.domain_name, self.access_key_id, self.access_key_secret
        )
        # 验证指纹比较被调用（两次：新证书和当前证书）
        self.assertEqual(mock_get_fingerprint.call_count, 2)

    @patch("main.is_cert_valid")
    @patch("main.CdnCertsRenewer.get_current_cert")
    @patch("main.CdnCertsRenewer.create_client")
    def test_renew_cert_force_update(
        self, mock_create_client, mock_get_current_cert, mock_is_cert_valid
    ):
        """测试强制更新模式（即使证书相同也更新）"""
        # 设置mock
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = "current_cert_content"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.set_cdn_domain_sslcertificate_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        # 执行测试（force=True）
        result = CdnCertsRenewer.renew_cert(
            self.domain_name,
            self.cert,
            self.cert_private_key,
            self.region,
            self.access_key_id,
            self.access_key_secret,
            force=True,
        )

        # 验证结果
        self.assertTrue(result)
        # 验证即使有当前证书，也执行了更新
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
        # 验证客户端类型
        self.assertIsInstance(client, Slb20140515Client)

    @patch("main.SlbCertsRenewer.get_current_cert_fingerprint")
    @patch("main.SlbCertsRenewer.create_client")
    def test_renew_cert_success(
        self, mock_create_client, mock_get_current_cert_fingerprint
    ):
        """测试证书更新成功"""
        # 设置mock
        mock_get_current_cert_fingerprint.return_value = None  # 没有当前证书，需要更新
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
        mock_get_current_cert_fingerprint.assert_called_once_with(
            self.instance_id,
            self.region,
            self.access_key_id,
            self.access_key_secret,
        )
        mock_client.upload_server_certificate_with_options.assert_called_once()

    @patch("main.SlbCertsRenewer.get_current_cert_fingerprint")
    @patch("main.get_cert_fingerprint_sha1")
    def test_renew_cert_skip_when_same(
        self, mock_get_fingerprint, mock_get_current_cert_fingerprint
    ):
        """测试证书相同时跳过更新"""
        # 设置mock
        mock_get_current_cert_fingerprint.return_value = "same:fingerprint:value"
        mock_get_fingerprint.return_value = "same:fingerprint:value"

        # 执行测试（默认 force=False）
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
        mock_get_current_cert_fingerprint.assert_called_once_with(
            self.instance_id,
            self.region,
            self.access_key_id,
            self.access_key_secret,
        )
        # 验证指纹比较被调用（一次：新证书）
        mock_get_fingerprint.assert_called_once_with(self.cert)

    @patch("main.SlbCertsRenewer.get_current_cert_fingerprint")
    @patch("main.SlbCertsRenewer.create_client")
    def test_renew_cert_force_update(
        self, mock_create_client, mock_get_current_cert_fingerprint
    ):
        """测试强制更新模式（即使证书相同也更新）"""
        # 设置mock
        mock_get_current_cert_fingerprint.return_value = "same:fingerprint:value"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = mock_response
        mock_create_client.return_value = mock_client

        # 执行测试（force=True）
        result = SlbCertsRenewer.renew_cert(
            self.instance_id,
            self.cert,
            self.cert_private_key,
            self.region,
            self.access_key_id,
            self.access_key_secret,
            force=True,
        )

        # 验证结果
        self.assertTrue(result)
        # 验证即使证书指纹相同，也执行了更新
        mock_client.upload_server_certificate_with_options.assert_called_once()


class TestLoadConfig(unittest.TestCase):
    """配置加载测试"""

    def setUp(self):
        """测试前准备"""
        # 清除环境变量
        self.original_env = os.environ.copy()
        # 确保清除可能影响测试的环境变量
        os.environ.pop("FORCE_UPDATE", None)

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
                "FORCE_UPDATE": "false",  # 显式设置为 false
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
        self.assertEqual(result[7], False)  # force 默认为 False

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
                "FORCE_UPDATE": "false",  # 显式设置为 false
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
        self.assertEqual(result[7], False)  # force 默认为 False

    def test_load_config_with_force_update(self):
        """测试加载配置时包含强制更新标志"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "test_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
                "FORCE_UPDATE": "true",
            }
        )

        result = load_config()
        self.assertEqual(result[7], True)  # force 为 True

    def test_load_config_with_force_update_false(self):
        """测试强制更新标志为 false"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "test_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
                "FORCE_UPDATE": "false",
            }
        )

        result = load_config()
        self.assertEqual(result[7], False)  # force 为 False

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
