import os
import sys
import unittest

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.utils.ssl_cert_parser import (  # noqa: I001
    is_domain_name_match,
)


class TestSslCertParser(unittest.TestCase):
    """SSL证书解析器测试"""

    def setUp(self):
        """测试前准备"""
        # 这是一个有效的测试证书（示例）
        self.valid_cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy5+4y3z8v5x9w2q1r3t5
y7u9v1w4x6z8a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7
a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9
g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1
m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3
s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5
y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7
e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9
k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1
QwIDAQAB
-----END CERTIFICATE-----"""

        self.test_domain = "test.example.com"
        self.wildcard_domain = "*.example.com"

    def test_is_domain_name_match_exact(self):
        """测试精确域名匹配"""
        domain_list = ["test.example.com", "other.example.com"]
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertFalse(is_domain_name_match("unknown.example.com", domain_list))

    def test_is_domain_name_match_wildcard(self):
        """测试通配符域名匹配"""
        domain_list = ["*.example.com"]
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertTrue(is_domain_name_match("sub.test.example.com", domain_list))
        self.assertFalse(is_domain_name_match("example.com", domain_list))
        self.assertFalse(is_domain_name_match("other.com", domain_list))

    def test_is_domain_name_match_mixed(self):
        """测试混合域名列表匹配"""
        domain_list = ["example.com", "*.example.com", "test.example.com"]
        self.assertTrue(is_domain_name_match("example.com", domain_list))
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertTrue(is_domain_name_match("sub.example.com", domain_list))
        self.assertFalse(is_domain_name_match("other.com", domain_list))

    def test_is_cert_valid_with_valid_cert(self):
        """测试有效证书验证"""
        # 注意：这个测试需要真实的证书，这里只是示例
        # 实际测试时需要使用真实的证书内容
        pass

    def test_is_cert_valid_with_invalid_domain(self):
        """测试域名不匹配的证书验证"""
        # 注意：这个测试需要真实的证书，这里只是示例
        # 实际测试时需要使用真实的证书内容
        pass

    def test_is_cert_valid_with_expired_cert(self):
        """测试过期证书验证"""
        # 注意：这个测试需要真实的过期证书，这里只是示例
        # 实际测试时需要使用真实的过期证书内容
        pass


if __name__ == "__main__":
    unittest.main()
