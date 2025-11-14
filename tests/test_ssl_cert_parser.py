import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.utils.ssl_cert_parser import (  # noqa: I001
    is_domain_name_match,
)

class TestSslCertParser(unittest.TestCase):
    """SSL certificate parser tests"""

    def setUp(self):
        """Test setup"""
        # This is a valid test certificate (example)
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
        """Test exact domain name matching"""
        domain_list = ["test.example.com", "other.example.com"]
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertFalse(is_domain_name_match("unknown.example.com", domain_list))

    def test_is_domain_name_match_wildcard(self):
        """Test wildcard domain name matching"""
        domain_list = ["*.example.com"]
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertTrue(is_domain_name_match("sub.test.example.com", domain_list))
        self.assertFalse(is_domain_name_match("example.com", domain_list))
        self.assertFalse(is_domain_name_match("other.com", domain_list))

    def test_is_domain_name_match_mixed(self):
        """Test mixed domain name list matching"""
        domain_list = ["example.com", "*.example.com", "test.example.com"]
        self.assertTrue(is_domain_name_match("example.com", domain_list))
        self.assertTrue(is_domain_name_match("test.example.com", domain_list))
        self.assertTrue(is_domain_name_match("sub.example.com", domain_list))
        self.assertFalse(is_domain_name_match("other.com", domain_list))

    def test_is_cert_valid_with_valid_cert(self):
        """Test valid certificate validation"""
        # Note: This test requires a real certificate, this is just an example
        # Actual testing should use real certificate content
        pass

    def test_is_cert_valid_with_invalid_domain(self):
        """Test certificate validation with mismatched domain"""
        # Note: This test requires a real certificate, this is just an example
        # Actual testing should use real certificate content
        pass

    def test_is_cert_valid_with_expired_cert(self):
        """Test expired certificate validation"""
        # Note: This test requires a real expired certificate, this is just an example
        # Actual testing should use real expired certificate content
        pass


if __name__ == "__main__":
    unittest.main()
