"""Integration tests for webhook functionality"""

import time
from unittest.mock import MagicMock, patch

import pytest

from cloud_cert_renewer.cert_renewer.cdn_renewer import CdnCertRenewerStrategy
from cloud_cert_renewer.cert_renewer.composite import CompositeCertRenewer
from cloud_cert_renewer.config.models import (
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
    WebhookConfig,
)


class TestWebhookIntegration:
    """Integration tests for webhook functionality"""

    @pytest.fixture
    def cdn_config(self):
        """Create CDN configuration for testing"""
        # Use valid test certificate from .env.example
        valid_cert = """-----BEGIN CERTIFICATE-----
MIIE8TCCA9mgAwIBAgISA48pSPsqSMyRseyWkKjqrgm3MA0GCSqGSIb3DQEBCwUA
MDIxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQswCQYDVQQD
EwJSMzAeFw0yMzEyMjgxMDA5NDRaFw0yNDAzMjcxMDA5NDNaMBcxFTATBgNVBAMM
DCouYW11Z3VhLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANHp
/APp/xK+oINkRFaTtXNomrGt+T2/u5tivBD74/tTghkBe9DCob6OmX3J4YsYg5Ll
WO+66o56ad4lUKJwdp6g2hulbw/T6SgI96R91XGgvnnhyz3T06H9HKE0aDwn9JQ8
cADpdIm0cYShPEik4S1aVBL16AH1HGqYXhxlBbVLUNoWLGAFqrEzFF/ZS04WEbPt
veWRIOWoqWFqqpFmMIfFodJvrIWbCSHuHIM8VdU6m6sjhJkP73mWcIrl0Wi7IZc2
f4G8u8I+WXCatmSfE80YtAJimi5fn+kXzSGR6IV9cdpYHqx3apdWc0vTVWqqyoul
l5d/+ijAUmkkr4PSwA0CAwEAAaOCAhowggIWMA4GA1UdDwEB/wQEAwIFoDAdBgNV
HSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwDAYDVR0TAQH/BAIwADAdBgNVHQ4E
FgQUDrvkV12XMK1bOSU/t32ZwQinNc8wHwYDVR0jBBgwFoAUFC6zF7dYVsuuUAlA
5h+vnYsUwsYwVQYIKwYBBQUHAQEESTBHMCEGCCsGAQUFBzABhhVodHRwOi8vcjMu
by5sZW5jci5vcmcwIgYIKwYBBQUHMAKGFmh0dHA6Ly9yMy5pLmxlbmNyLm9yZy8w
IwYDVR0RBBwwGoIMKi5hbXVndWEuY29tggphbXVndWEuY29tMBMGA1UdIAQMMAow
CAYGZ4EMAQIBMIIBBAYKKwYBBAHWeQIEAgSB9QSB8gDwAHcASLDja9qmRzQP5WoC
+p0w6xxSActW3SyB2bu/qznYhHMAAAGMsB2tkAAABAMASDBGAiEA1BBlKNkEupcj
B5+wd1AsPkDrr0eGPxsd/pBosdFWlL0CIQD7drlb1BxF/DjDb6DPqjk4VLJuqJ68
z74p+1SpahYjRgB1ADtTd3U+LbmAToswWwb+QDtn2E/D9Me9AA0tcm/h+tQXAAAB
jLAdrZMAAAQDAEYwRAIgRi3sbBP8P6Onuf+A18ncDxbMin3xmBm7OhWw2UjEV80C
IEYpfT2myi/iYexBTEHBjVHa7qHZ5hoY69gkEImPJvPTMA0GCSqGSIb3DQEBCwUA
A4IBAQBpxyjlL9G5doUmLykjat7jpKeC6OC1dC+lZeE09aRXXp5VnuyATe3A9pPW
WiumjlnpbuZ5T43km3CQ4zBZSHv5fqnCjcopn6t2N+edFVytmyjZcJ13PSzSz5R7
CGwEyc185MntDtvzkMlXVvcV6x6SMghFb3uP138i/0eMRs8CZPVYAYKq98OopCn6
dL7AZNiJQxGQ5WkFFiuHTWz5fC/OOMIme567guxXruYHkdCyhAkoIs06pOC/p4DD
ygfSNN03BTEoQ7T16vzhtMpofkk/gXZb6CXEX5ckBjg0CM9I1Xf8BZAfbJMfdqOr
AIqjJU+SsN/cwkfCEPVkY02qfDZz
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFFjCCAv6gAwIBAgIRAJErCErPDBinU/bWLiWnX1owDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMjAwOTA0MDAwMDAw
WhcNMjUwOTE1MTYwMDAwWjAyMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNTGV0J3Mg
RW5jcnlwdDELMAkGA1UEAxMCUjMwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQC7AhUozPaglNMPEuyNVZLD+ILxmaZ6QoinXSaqtSu5xUyxr45r+XXIo9cP
R5QUVTVXjJ6oojkZ9YI8QqlObvU7wy7bjcCwXPNZOOftz2nwWgsbvsCUJCWH+jdx
sxPnHKzhm+/b5DtFUkWWqcFTzjTIUu61ru2P3mBw4qVUq7ZtDpelQDRrK9O8Zutm
NHz6a4uPVymZ+DAXXbpyb/uBxa3Shlg9F8fnCbvxK/eG3MHacV3URuPMrSXBiLxg
Z3Vms/EY96Jc5lP/Ooi2R6X/ExjqmAl3P51T+c8B5fWmcBcUr2Ok/5mzk53cU6cG
/kiFHaFpriV1uxPMUgP17VGhi9sVAgMBAAGjggEIMIIBBDAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMBMBIGA1UdEwEB/wQIMAYB
Af8CAQAwHQYDVR0OBBYEFBQusxe3WFbLrlAJQOYfr52LFMLGMB8GA1UdIwQYMBaA
FHm0WeZ7tuXkAXOACIjIGlj26ZtuMDIGCCsGAQUFBwEBBCYwJDAiBggrBgEFBQcw
AoYWaHR0cDovL3gxLmkubGVuY3Iub3JnLzAnBgNVHR8EIDAeMBygGqAYhhZodHRw
Oi8veDEuYy5sZW5jci5vcmcvMCIGA1UdIAQbMBkwCAYGZ4EMAQIBMA0GCysGAQQB
gt8TAQEBMA0GCSqGSIb3DQEBCwUAA4ICAQCFyk5HPqP3hUSFvNVneLKYY611TR6W
PTNlclQtgaDqw+34IL9fzLdwALduO/ZelN7kIJ+m74uyA+eitRY8kc607TkC53wl
ikfmZW4/RvTZ8M6UK+5UzhK8jCdLuMGYL6KvzXGRSgi3yLgjewQtCPkIVz6D2QQz
CkcheAmCJ8MqyJu5zlzyZMjAvnnAT45tRAxekrsu94sQ4egdRCnbWSDtY7kh+BIm
lJNXoB1lBMEKIq4QDUOXoRgffuDghje1WrG9ML+Hbisq/yFOGwXD9RiX8F6sw6W4
avAuvDszue5L3sz85K+EC4Y/wFVDNvZo4TYXao6Z0f+lQKc0t8DQYzk1OXVu8rp2
yJMC6alLbBfODALZvYH7n7do1AZls4I9d1P4jnkDrQoxB3UqQ9hVl3LEKQ73xF1O
yK5GhDDX8oVfGKF5u+decIsH4YaTw7mP3GFxJSqv3+0lUFJoi5Lc5da149p90Ids
hCExroL1+7mryIkXPeFM5TgO9r0rvZaBFOvV2z0gp35Z0+L4WPlbuEjN/lxPFin+
HlUjr8gRsI3qfJOQFy/9rKIJR0Y/8Omwt/8oTWgy1mdeHmmjk7j1nYsvC9JSQ6Zv
MldlTTKB3zhThV1+XWYp6rjd5JW1zbVWEkLNxE7GJThEUG3szgBVGP7pSWTUTsqX
nLRbwHOoq7hHwg==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFYDCCBEigAwIBAgIQQAF3ITfU6UK47naqPGQKtzANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTIxMDEyMDE5MTQwM1oXDTI0MDkzMDE4MTQwM1ow
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwggIiMA0GCSqGSIb3DQEB
AQUAA4ICDwAwggIKAoICAQCt6CRz9BQ385ueK1coHIe+3LffOJCMbjzmV6B493XC
ov71am72AE8o295ohmxEk7axY/0UEmu/H9LqMZshftEzPLpI9d1537O4/xLxIZpL
wYqGcWlKZmZsj348cL+tKSIG8+TA5oCu4kuPt5l+lAOf00eXfJlII1PoOK5PCm+D
LtFJV4yAdLbaL9A4jXsDcCEbdfIwPPqPrt3aY6vrFk/CjhFLfs8L6P+1dy70sntK
4EwSJQxwjQMpoOFTJOwT2e4ZvxCzSow/iaNhUd6shweU9GNx7C7ib1uYgeGJXDR5
bHbvO5BieebbpJovJsXQEOEO3tkQjhb7t/eo98flAgeYjzYIlefiN5YNNnWe+w5y
sR2bvAP5SQXYgd0FtCrWQemsAXaVCg/Y39W9Eh81LygXbNKYwagJZHduRze6zqxZ
Xmidf3LWicUGQSk+WT7dJvUkyRGnWqNMQB9GoZm1pzpRboY7nn1ypxIFeFntPlF4
FQsDj43QLwWyPntKHEtzBRL8xurgUBN8Q5N0s8p0544fAQjQMNRbcTa0B7rBMDBc
SLeCO5imfWCKoqMpgsy6vYMEG6KDA0Gh1gXxG8K28Kh8hjtGqEgqiNx2mna/H2ql
PRmP6zjzZN7IKw0KKP/32+IVQtQi0Cdd4Xn+GOdwiK1O5tmLOsbdJ1Fu/7xk9TND
TwIDAQABo4IBRjCCAUIwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMCAQYw
SwYIKwYBBQUHAQEEPzA9MDsGCCsGAQUFBzAChi9odHRwOi8vYXBwcy5pZGVudHJ1
c3QuY29tL3Jvb3RzL2RzdHJvb3RjYXgzLnA3YzAfBgNVHSMEGDAWgBTEp7Gkeyxx
+tvhS5B1/8QVYIWJEDBUBgNVHSAETTBLMAgGBmeBDAECATA/BgsrBgEEAYLfEwEB
ATAwMC4GCCsGAQUFBwIBFiJodHRwOi8vY3BzLnJvb3QteDEubGV0c2VuY3J5cHQu
b3JnMDwGA1UdHwQ1MDMwMaAvoC2GK2h0dHA6Ly9jcmwuaWRlbnRydXN0LmNvbS9E
U1RST09UQ0FYM0NSTC5jcmwwHQYDVR0OBBYEFHm0WeZ7tuXkAXOACIjIGlj26Ztu
MA0GCSqGSIb3DQEBCwUAA4IBAQAKcwBslm7/DlLQrt2M51oGrS+o44+/yQoDFVDC
5WxCu2+b9LRPwkSICHXM6webFGJueN7sJ7o5XPWioW5WlHAQU7G75K/QosMrAdSW
9MUgNTP52GE24HGNtLi1qoJFlcDyqSMo59ahy2cI2qBDLKobkx/J3vWraV0T9VuG
WCLKTVXkcGdtwlfFRjlBz4pYg1htmf5X6DYO8A4jqv2Il9DjXA6USbW1FzXSLr9O
he8Y4IWS6wY7bCkjCWDcRQJMEhg76fsO3txE+FiYruq9RUWhiF1myv4Q6W+CyBFC
Dfvp7OOGAN6dEOM4+qR9sdjoSYKEBpsr6GtPAQw4dy753ec5
-----END CERTIFICATE-----"""
        valid_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA0en8A+n/Er6gg2REVpO1c2iasa35Pb+7m2K8EPvj+1OCGQF7
0MKhvo6ZfcnhixiDkuVY77rqjnpp3iVQonB2nqDaG6VvD9PpKAj3pH3VcaC+eeHL
PdPTof0coTRoPCf0lDxwAOl0ibRxhKE8SKThLVpUEvXoAfUcapheHGUFtUtQ2hYs
YAWqsTMUX9lLThYRs+295ZEg5aipYWqqkWYwh8Wh0m+shZsJIe4cgzxV1TqbqyOE
mQ/veZZwiuXRaLshlzZ/gby7wj5ZcJq2ZJ8TzRi0AmKaLl+f6RfNIZHohX1x2lge
rHdql1ZzS9NVaqrKi6WXl3/6KMBSaSSvg9LADQIDAQABAoIBAQCYUjXxkSbqrzFC
psuAF4cfy9QVAq1NxYeZZbgaiu4QPbS1+IGkJte/szJmOMxVZuBzA8HZk8UIxoN0
E5fDh+BLk2UxkoZY8ejKiFdLIZR087PENbiJkOCNN2JDCAhrPoMX3hNYVg+erTWC
jI12GU7c3iML7yz/3qFUKGSCLjxKJKCEVD73+pRXfC4GyjPfXBiqedCrMWZbgTOx
DZo8oyIk0k818xKs0Ke1vlIWWEmpbuw0BABEdwSThhbgmpIRjYBkVVCDuYpfHe+v
KMN6gAbStWcxuIqeJ+93A09utZilnt7D6UvLhTbQhGY1Y/mqzdxAoU0j+MTxa1jX
imMBGSZxAoGBAOdRB9qkd6xJ1gD6RcmOBiQRm6FZ677WiqvL85Fm6K2wi1a7DknH
mq+nyQyH744EegGaGGilsrUdOWVHnf4hpSv66M1UUiNEWDYdtxpn+DNJkxFxRWlC
OJnXuQymNEH/E0IF7xqKKYQLsqRV6iaJg1u2Z93QBXicGPV9yvUOuO0DAoGBAOhQ
SslNK7I17BClazoJ4DZK3SbKH0qxADypdkMp8dCSxf7+ef53RUs1rpdq49/FmGnR
ZGcpQ4483lr2L7dOaL3PWQ+D5sMqanCvJ0sX3yJjdXmz7vsDF6QJN0UGcFKYdi2p
WEl222ZPX+baH0chtga7PjYfYq+pCDQ6mCMsO+mvAoGBAI3B7+FDN3/jQ/4XYltR
6VuDWu/37mxmiFceRydNfLys28eMHQaEB70sQx6l094hyi9fIyRGn4002q7BxAYw
0ktwmejzit7IDJMlhMfu/YFYzoM6+oG2Ln/BX0tsM8xaKJAmmNCX6Tdd/92MNVHm
phS3ZVHfIOs4JmeT7qRdoGDHAoGBAJJZcqOZ7/sWqR5bd09axVqukt9K2aeuFd4h
S5VIKUQiEoVvPt8luAuHR/OvrNpdmoSfGsc6YYqLofBfwvORe76Hjy2NBKTSZbeT
QAe4hCMf0PPYfKa47f2yqJTdV4lQ7rIZSrsNG246dsnxg17GR+u5rZle8EaFD9wH
Raxyw1OVAoGAakA6wO6AQeh9ZzvAiel8x4je2AnudDA6B0yb+O3XC6EpoZw+//k4
/Lo53pBurzxEFk1FHqdw+kHsuy94UPUUqWsoL4hCQG9MUpvNd9yS11FDJOydc51M
tkNkku9BXJFJy5bAVs9NxLLOs2OI+REJykbT9zBMiOkAeeFppKYP+qU=
-----END RSA PRIVATE KEY-----"""
        return CdnConfig(
            domain_names=["example.com"],
            cert=valid_cert,
            cert_private_key=valid_key,
            region="cn-hangzhou",
        )

    @pytest.fixture
    def lb_config(self):
        """Create Load Balancer configuration for testing"""
        # Use valid test certificate from .env.example
        valid_cert = """-----BEGIN CERTIFICATE-----
MIIE8TCCA9mgAwIBAgISA48pSPsqSMyRseyWkKjqrgm3MA0GCSqGSIb3DQEBCwUA
MDIxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQswCQYDVQQD
EwJSMzAeFw0yMzEyMjgxMDA5NDRaFw0yNDAzMjcxMDA5NDNaMBcxFTATBgNVBAMM
DCouYW11Z3VhLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANHp
/APp/xK+oINkRFaTtXNomrGt+T2/u5tivBD74/tTghkBe9DCob6OmX3J4YsYg5Ll
WO+66o56ad4lUKJwdp6g2hulbw/T6SgI96R91XGgvnnhyz3T06H9HKE0aDwn9JQ8
cADpdIm0cYShPEik4S1aVBL16AH1HGqYXhxlBbVLUNoWLGAFqrEzFF/ZS04WEbPt
veWRIOWoqWFqqpFmMIfFodJvrIWbCSHuHIM8VdU6m6sjhJkP73mWcIrl0Wi7IZc2
f4G8u8I+WXCatmSfE80YtAJimi5fn+kXzSGR6IV9cdpYHqx3apdWc0vTVWqqyoul
l5d/+ijAUmkkr4PSwA0CAwEAAaOCAhowggIWMA4GA1UdDwEB/wQEAwIFoDAdBgNV
HSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwDAYDVR0TAQH/BAIwADAdBgNVHQ4E
FgQUDrvkV12XMK1bOSU/t32ZwQinNc8wHwYDVR0jBBgwFoAUFC6zF7dYVsuuUAlA
5h+vnYsUwsYwVQYIKwYBBQUHAQEESTBHMCEGCCsGAQUFBzABhhVodHRwOi8vcjMu
by5sZW5jci5vcmcwIgYIKwYBBQUHMAKGFmh0dHA6Ly9yMy5pLmxlbmNyLm9yZy8w
IwYDVR0RBBwwGoIMKi5hbXVndWEuY29tggphbXVndWEuY29tMBMGA1UdIAQMMAow
CAYGZ4EMAQIBMIIBBAYKKwYBBAHWeQIEAgSB9QSB8gDwAHcASLDja9qmRzQP5WoC
+p0w6xxSActW3SyB2bu/qznYhHMAAAGMsB2tkAAABAMASDBGAiEA1BBlKNkEupcj
B5+wd1AsPkDrr0eGPxsd/pBosdFWlL0CIQD7drlb1BxF/DjDb6DPqjk4VLJuqJ68
z74p+1SpahYjRgB1ADtTd3U+LbmAToswWwb+QDtn2E/D9Me9AA0tcm/h+tQXAAAB
jLAdrZMAAAQDAEYwRAIgRi3sbBP8P6Onuf+A18ncDxbMin3xmBm7OhWw2UjEV80C
IEYpfT2myi/iYexBTEHBjVHa7qHZ5hoY69gkEImPJvPTMA0GCSqGSIb3DQEBCwUA
A4IBAQBpxyjlL9G5doUmLykjat7jpKeC6OC1dC+lZeE09aRXXp5VnuyATe3A9pPW
WiumjlnpbuZ5T43km3CQ4zBZSHv5fqnCjcopn6t2N+edFVytmyjZcJ13PSzSz5R7
CGwEyc185MntDtvzkMlXVvcV6x6SMghFb3uP138i/0eMRs8CZPVYAYKq98OopCn6
dL7AZNiJQxGQ5WkFFiuHTWz5fC/OOMIme567guxXruYHkdCyhAkoIs06pOC/p4DD
ygfSNN03BTEoQ7T16vzhtMpofkk/gXZb6CXEX5ckBjg0CM9I1Xf8BZAfbJMfdqOr
AIqjJU+SsN/cwkfCEPVkY02qfDZz
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFFjCCAv6gAwIBAgIRAJErCErPDBinU/bWLiWnX1owDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMjAwOTA0MDAwMDAw
WhcNMjUwOTE1MTYwMDAwWjAyMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNTGV0J3Mg
RW5jcnlwdDELMAkGA1UEAxMCUjMwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQC7AhUozPaglNMPEuyNVZLD+ILxmaZ6QoinXSaqtSu5xUyxr45r+XXIo9cP
R5QUVTVXjJ6oojkZ9YI8QqlObvU7wy7bjcCwXPNZOOftz2nwWgsbvsCUJCWH+jdx
sxPnHKzhm+/b5DtFUkWWqcFTzjTIUu61ru2P3mBw4qVUq7ZtDpelQDRrK9O8Zutm
NHz6a4uPVymZ+DAXXbpyb/uBxa3Shlg9F8fnCbvxK/eG3MHacV3URuPMrSXBiLxg
Z3Vms/EY96Jc5lP/Ooi2R6X/ExjqmAl3P51T+c8B5fWmcBcUr2Ok/5mzk53cU6cG
/kiFHaFpriV1uxPMUgP17VGhi9sVAgMBAAGjggEIMIIBBDAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMBMBIGA1UdEwEB/wQIMAYB
Af8CAQAwHQYDVR0OBBYEFBQusxe3WFbLrlAJQOYfr52LFMLGMB8GA1UdIwQYMBaA
FHm0WeZ7tuXkAXOACIjIGlj26ZtuMDIGCCsGAQUFBwEBBCYwJDAiBggrBgEFBQcw
AoYWaHR0cDovL3gxLmkubGVuY3Iub3JnLzAnBgNVHR8EIDAeMBygGqAYhhZodHRw
Oi8veDEuYy5sZW5jci5vcmcvMCIGA1UdIAQbMBkwCAYGZ4EMAQIBMA0GCysGAQQB
gt8TAQEBMA0GCSqGSIb3DQEBCwUAA4ICAQCFyk5HPqP3hUSFvNVneLKYY611TR6W
PTNlclQtgaDqw+34IL9fzLdwALduO/ZelN7kIJ+m74uyA+eitRY8kc607TkC53wl
ikfmZW4/RvTZ8M6UK+5UzhK8jCdLuMGYL6KvzXGRSgi3yLgjewQtCPkIVz6D2QQz
CkcheAmCJ8MqyJu5zlzyZMjAvnnAT45tRAxekrsu94sQ4egdRCnbWSDtY7kh+BIm
lJNXoB1lBMEKIq4QDUOXoRgffuDghje1WrG9ML+Hbisq/yFOGwXD9RiX8F6sw6W4
avAuvDszue5L3sz85K+EC4Y/wFVDNvZo4TYXao6Z0f+lQKc0t8DQYzk1OXVu8rp2
yJMC6alLbBfODALZvYH7n7do1AZls4I9d1P4jnkDrQoxB3UqQ9hVl3LEKQ73xF1O
yK5GhDDX8oVfGKF5u+decIsH4YaTw7mP3GFxJSqv3+0lUFJoi5Lc5da149p90Ids
hCExroL1+7mryIkXPeFM5TgO9r0rvZaBFOvV2z0gp35Z0+L4WPlbuEjN/lxPFin+
HlUjr8gRsI3qfJOQFy/9rKIJR0Y/8Omwt/8oTWgy1mdeHmmjk7j1nYsvC9JSQ6Zv
MldlTTKB3zhThV1+XWYp6rjd5JW1zbVWEkLNxE7GJThEUG3szgBVGP7pSWTUTsqX
nLRbwHOoq7hHwg==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFYDCCBEigAwIBAgIQQAF3ITfU6UK47naqPGQKtzANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTIxMDEyMDE5MTQwM1oXDTI0MDkzMDE4MTQwM1ow
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwggIiMA0GCSqGSIb3DQEB
AQUAA4ICDwAwggIKAoICAQCt6CRz9BQ385ueK1coHIe+3LffOJCMbjzmV6B493XC
ov71am72AE8o295ohmxEk7axY/0UEmu/H9LqMZshftEzPLpI9d1537O4/xLxIZpL
wYqGcWlKZmZsj348cL+tKSIG8+TA5oCu4kuPt5l+lAOf00eXfJlII1PoOK5PCm+D
LtFJV4yAdLbaL9A4jXsDcCEbdfIwPPqPrt3aY6vrFk/CjhFLfs8L6P+1dy70sntK
4EwSJQxwjQMpoOFTJOwT2e4ZvxCzSow/iaNhUd6shweU9GNx7C7ib1uYgeGJXDR5
bHbvO5BieebbpJovJsXQEOEO3tkQjhb7t/eo98flAgeYjzYIlefiN5YNNnWe+w5y
sR2bvAP5SQXYgd0FtCrWQemsAXaVCg/Y39W9Eh81LygXbNKYwagJZHduRze6zqxZ
Xmidf3LWicUGQSk+WT7dJvUkyRGnWqNMQB9GoZm1pzpRboY7nn1ypxIFeFntPlF4
FQsDj43QLwWyPntKHEtzBRL8xurgUBN8Q5N0s8p0544fAQjQMNRbcTa0B7rBMDBc
SLeCO5imfWCKoqMpgsy6vYMEG6KDA0Gh1gXxG8K28Kh8hjtGqEgqiNx2mna/H2ql
PRmP6zjzZN7IKw0KKP/32+IVQtQi0Cdd4Xn+GOdwiK1O5tmLOsbdJ1Fu/7xk9TND
TwIDAQABo4IBRjCCAUIwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMCAQYw
SwYIKwYBBQUHAQEEPzA9MDsGCCsGAQUFBzAChi9odHRwOi8vYXBwcy5pZGVudHJ1
c3QuY29tL3Jvb3RzL2RzdHJvb3RjYXgzLnA3YzAfBgNVHSMEGDAWgBTEp7Gkeyxx
+tvhS5B1/8QVYIWJEDBUBgNVHSAETTBLMAgGBmeBDAECATA/BgsrBgEEAYLfEwEB
ATAwMC4GCCsGAQUFBwIBFiJodHRwOi8vY3BzLnJvb3QteDEubGV0c2VuY3J5cHQu
b3JnMDwGA1UdHwQ1MDMwMaAvoC2GK2h0dHA6Ly9jcmwuaWRlbnRydXN0LmNvbS9E
U1RST09UQ0FYM0NSTC5jcmwwHQYDVR0OBBYEFHm0WeZ7tuXkAXOACIjIGlj26Ztu
MA0GCSqGSIb3DQEBCwUAA4IBAQAKcwBslm7/DlLQrt2M51oGrS+o44+/yQoDFVDC
5WxCu2+b9LRPwkSICHXM6webFGJueN7sJ7o5XPWioW5WlHAQU7G75K/QosMrAdSW
9MUgNTP52GE24HGNtLi1qoJFlcDyqSMo59ahy2cI2qBDLKobkx/J3vWraV0T9VuG
WCLKTVXkcGdtwlfFRjlBz4pYg1htmf5X6DYO8A4jqv2Il9DjXA6USbW1FzXSLr9O
he8Y4IWS6wY7bCkjCWDcRQJMEhg76fsO3txE+FiYruq9RUWhiF1myv4Q6W+CyBFC
Dfvp7OOGAN6dEOM4+qR9sdjoSYKEBpsr6GtPAQw4dy753ec5
-----END CERTIFICATE-----"""
        valid_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA0en8A+n/Er6gg2REVpO1c2iasa35Pb+7m2K8EPvj+1OCGQF7
0MKhvo6ZfcnhixiDkuVY77rqjnpp3iVQonB2nqDaG6VvD9PpKAj3pH3VcaC+eeHL
PdPTof0coTRoPCf0lDxwAOl0ibRxhKE8SKThLVpUEvXoAfUcapheHGUFtUtQ2hYs
YAWqsTMUX9lLThYRs+295ZEg5aipYWqqkWYwh8Wh0m+shZsJIe4cgzxV1TqbqyOE
mQ/veZZwiuXRaLshlzZ/gby7wj5ZcJq2ZJ8TzRi0AmKaLl+f6RfNIZHohX1x2lge
rHdql1ZzS9NVaqrKi6WXl3/6KMBSaSSvg9LADQIDAQABAoIBAQCYUjXxkSbqrzFC
psuAF4cfy9QVAq1NxYeZZbgaiu4QPbS1+IGkJte/szJmOMxVZuBzA8HZk8UIxoN0
E5fDh+BLk2UxkoZY8ejKiFdLIZR087PENbiJkOCNN2JDCAhrPoMX3hNYVg+erTWC
jI12GU7c3iML7yz/3qFUKGSCLjxKJKCEVD73+pRXfC4GyjPfXBiqedCrMWZbgTOx
DZo8oyIk0k818xKs0Ke1vlIWWEmpbuw0BABEdwSThhbgmpIRjYBkVVCDuYpfHe+v
KMN6gAbStWcxuIqeJ+93A09utZilnt7D6UvLhTbQhGY1Y/mqzdxAoU0j+MTxa1jX
imMBGSZxAoGBAOdRB9qkd6xJ1gD6RcmOBiQRm6FZ677WiqvL85Fm6K2wi1a7DknH
mq+nyQyH744EegGaGGilsrUdOWVHnf4hpSv66M1UUiNEWDYdtxpn+DNJkxFxRWlC
OJnXuQymNEH/E0IF7xqKKYQLsqRV6iaJg1u2Z93QBXicGPV9yvUOuO0DAoGBAOhQ
SslNK7I17BClazoJ4DZK3SbKH0qxADypdkMp8dCSxf7+ef53RUs1rpdq49/FmGnR
ZGcpQ4483lr2L7dOaL3PWQ+D5sMqanCvJ0sX3yJjdXmz7vsDF6QJN0UGcFKYdi2p
WEl222ZPX+baH0chtga7PjYfYq+pCDQ6mCMsO+mvAoGBAI3B7+FDN3/jQ/4XYltR
6VuDWu/37mxmiFceRydNfLys28eMHQaEB70sQx6l094hyi9fIyRGn4002q7BxAYw
0ktwmejzit7IDJMlhMfu/YFYzoM6+oG2Ln/BX0tsM8xaKJAmmNCX6Tdd/92MNVHm
phS3ZVHfIOs4JmeT7qRdoGDHAoGBAJJZcqOZ7/sWqR5bd09axVqukt9K2aeuFd4h
S5VIKUQiEoVvPt8luAuHR/OvrNpdmoSfGsc6YYqLofBfwvORe76Hjy2NBKTSZbeT
QAe4hCMf0PPYfKa47f2yqJTdV4lQ7rIZSrsNG246dsnxg17GR+u5rZle8EaFD9wH
Raxyw1OVAoGAakA6wO6AQeh9ZzvAiel8x4je2AnudDA6B0yb+O3XC6EpoZw+//k4
/Lo53pBurzxEFk1FHqdw+kHsuy94UPUUqWsoL4hCQG9MUpvNd9yS11FDJOydc51M
tkNkku9BXJFJy5bAVs9NxLLOs2OI+REJykbT9zBMiOkAeeFppKYP+qU=
-----END RSA PRIVATE KEY-----"""
        return LoadBalancerConfig(
            instance_ids=["lb-12345"],
            listener_port=443,
            cert=valid_cert,
            cert_private_key=valid_key,
            region="cn-hangzhou",
        )

    @pytest.fixture
    def webhook_config(self):
        """Create webhook configuration for testing"""
        return WebhookConfig(
            url="https://example.com/webhook",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def app_config_cdn(self, cdn_config, webhook_config):
        """Create full app config for CDN"""
        return AppConfig(
            service_type="cdn",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=Credentials(
                access_key_id="test_key",
                access_key_secret="test_secret",
            ),
            cdn_config=cdn_config,
            webhook_config=webhook_config,
            force_update=False,  # Explicitly set to False for skip tests
        )

    @pytest.fixture
    def app_config_lb(self, lb_config, webhook_config):
        """Create full app config for Load Balancer"""
        return AppConfig(
            service_type="lb",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=Credentials(
                access_key_id="test_key",
                access_key_secret="test_secret",
            ),
            lb_config=lb_config,
            webhook_config=webhook_config,
        )

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.base.BaseCertRenewer.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    def test_cdn_renewer_webhook_success(
        self,
        mock_do_renew,
        mock_get_fingerprint,
        mock_is_cert_valid,
        mock_client_class,
        app_config_cdn,
    ):
        """Test CDN renewer sends webhook on successful renewal"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_fingerprint.return_value = (
            None  # No current cert, will proceed with renewal
        )
        mock_do_renew.return_value = True

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config_cdn, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify renewal succeeded
        assert result is True

        # Wait a bit for async webhook calls
        time.sleep(0.1)

        # Verify webhook was sent for renewal_started and renewal_success
        assert mock_client.deliver.call_count == 2

        # Check first call (renewal_started)
        first_call_args = mock_client.deliver.call_args_list[0]
        first_payload = first_call_args[0][1]
        assert first_payload["event_type"] == "renewal_started"
        assert first_payload["source"]["service_type"] == "cdn"
        assert first_payload["target"]["domain_names"] == ["example.com"]

        # Check second call (renewal_success)
        second_call_args = mock_client.deliver.call_args_list[1]
        second_payload = second_call_args[0][1]
        assert second_payload["event_type"] == "renewal_success"
        assert second_payload["result"]["status"] == "success"

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.base.BaseCertRenewer.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    def test_cdn_renewer_webhook_failure(
        self,
        mock_do_renew,
        mock_get_fingerprint,
        mock_is_cert_valid,
        mock_client_class,
        app_config_cdn,
    ):
        """Test CDN renewer sends webhook on failed renewal"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_fingerprint.return_value = (
            None  # No current cert, will proceed with renewal
        )
        mock_do_renew.return_value = False

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config_cdn, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify renewal failed
        assert result is False

        # Wait a bit for async webhook calls
        time.sleep(0.1)

        # Verify webhook was sent for renewal_started and renewal_failed
        assert mock_client.deliver.call_count == 2

        # Check failure webhook payload
        failure_call_args = mock_client.deliver.call_args_list[1]
        failure_payload = failure_call_args[0][1]
        assert failure_payload["event_type"] == "renewal_failed"
        assert failure_payload["result"]["status"] == "failure"
        assert failure_payload["result"]["error_code"] == "RENEWAL_FAILED"

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch("cloud_cert_renewer.providers.base.CloudAdapterFactory.create")
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._calculate_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy.get_current_cert_fingerprint"
    )
    def test_cdn_renewer_webhook_skipped(
        self,
        mock_get_fingerprint,
        mock_do_renew,
        mock_calc_fingerprint,
        mock_adapter_factory,
        mock_is_cert_valid,
        mock_client_class,
        app_config_cdn,
    ):
        """Test CDN renewer sends webhook when certificate is skipped"""
        # Ensure force_update is False for skip logic to work
        app_config_cdn.force_update = False

        # Setup mocks for skip scenario
        mock_is_cert_valid.return_value = True
        mock_calc_fingerprint.return_value = "current_fingerprint"  # Same fingerprint
        mock_get_fingerprint.return_value = (
            "current_fingerprint"  # Current fingerprint matches new
        )
        # _do_renew should not be called when fingerprints match,
        # but mock it just in case
        mock_do_renew.return_value = True

        # Mock adapter factory to avoid actual API calls
        mock_adapter = MagicMock()
        mock_adapter.get_current_cdn_certificate.return_value = None
        mock_adapter_factory.return_value = mock_adapter

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config_cdn, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify renewal was skipped but returns True
        assert result is True

        # Wait a bit for async webhook calls
        time.sleep(0.2)

        # Verify webhook was sent for renewal_started and renewal_skipped
        call_count = mock_client.deliver.call_count
        assert call_count == 2, f"Expected 2 webhook calls, got {call_count}"

        # Check webhook payloads (order may vary due to async execution)
        event_types = []
        skip_payload = None
        for call in mock_client.deliver.call_args_list:
            payload = call[0][1] if call[0] else {}
            event_type = payload.get("event_type")
            event_types.append(event_type)
            if event_type == "renewal_skipped":
                skip_payload = payload

        # Verify both events were sent
        assert "renewal_started" in event_types
        assert "renewal_skipped" in event_types

        # Check skip webhook payload
        assert skip_payload is not None, "renewal_skipped event not found"
        assert skip_payload["event_type"] == "renewal_skipped"
        assert skip_payload["result"]["status"] == "skipped"
        assert "unchanged" in skip_payload["result"]["message"]

        # Verify get_current_cert_fingerprint was called
        assert mock_get_fingerprint.called

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch("cloud_cert_renewer.providers.base.CloudAdapterFactory.create")
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._calculate_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy.get_current_cert_fingerprint"
    )
    def test_cdn_renewer_webhook_skipped_with_all_events(
        self,
        mock_get_fingerprint,
        mock_do_renew,
        mock_calc_fingerprint,
        mock_adapter_factory,
        mock_is_cert_valid,
        mock_client_class,
        app_config_cdn,
    ):
        """Test webhook with enabledEvents=all when certificate is skipped.

        Verifies that webhook events are sent even when enabledEvents contains 'all'.
        """
        # Setup webhook config with enabledEvents=all
        app_config_cdn.webhook_config.enabled_events = {"all"}
        # Ensure force_update is False for skip logic to work
        app_config_cdn.force_update = False

        # Setup mocks for skip scenario
        mock_is_cert_valid.return_value = True
        mock_calc_fingerprint.return_value = "current_fingerprint"  # Same fingerprint
        mock_get_fingerprint.return_value = (
            "current_fingerprint"  # Current fingerprint matches new
        )
        # _do_renew should not be called when fingerprints match,
        # but mock it just in case
        mock_do_renew.return_value = True

        # Mock adapter factory to avoid actual API calls
        mock_adapter = MagicMock()
        mock_adapter.get_current_cdn_certificate.return_value = None
        mock_adapter_factory.return_value = mock_adapter

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config_cdn, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify renewal was skipped but returns True
        assert result is True

        # Wait a bit for async webhook calls
        time.sleep(0.2)

        # Verify webhook was sent for renewal_started and renewal_skipped
        call_count = mock_client.deliver.call_count
        assert call_count == 2, f"Expected 2 webhook calls, got {call_count}"

        # Check webhook payloads (order may vary due to async execution)
        event_types = []
        skip_payload = None
        for call in mock_client.deliver.call_args_list:
            payload = call[0][1] if call[0] else {}
            event_type = payload.get("event_type")
            event_types.append(event_type)
            if event_type == "renewal_skipped":
                skip_payload = payload

        # Verify both events were sent
        assert "renewal_started" in event_types
        assert "renewal_skipped" in event_types

        # Check skip webhook payload
        assert skip_payload is not None, "renewal_skipped event not found"
        assert skip_payload["event_type"] == "renewal_skipped"
        assert skip_payload["result"]["status"] == "skipped"
        assert "unchanged" in skip_payload["result"]["message"]

        # Verify get_current_cert_fingerprint was called
        assert mock_get_fingerprint.called

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    def test_cdn_renewer_webhook_dry_run(
        self, mock_is_cert_valid, mock_client_class, app_config_cdn
    ):
        """Test CDN renewer sends webhook for dry run"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        app_config_cdn.dry_run = True

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config_cdn, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify dry run succeeded
        assert result is True

        # Wait a bit for async webhook calls
        time.sleep(0.1)

        # Verify webhook was sent for renewal_started and renewal_success (dry run)
        assert mock_client.deliver.call_count == 2

        # Check dry run success webhook payload
        success_call_args = mock_client.deliver.call_args_list[1]
        success_payload = success_call_args[0][1]
        assert success_payload["event_type"] == "renewal_success"
        assert success_payload["result"]["status"] == "success"
        assert "DRY-RUN" in success_payload["result"]["message"]
        assert success_payload["metadata"]["dry_run"] is True

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.base.BaseCertRenewer.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    def test_composite_renewer_batch_webhook(
        self, mock_do_renew, mock_get_fingerprint, mock_is_cert_valid, mock_client_class
    ):
        """Test CompositeCertRenewer sends batch summary webhook"""
        # Create configs for multiple domains
        webhook_config = WebhookConfig(url="https://example.com/webhook")

        # Create multiple CDN configs
        # Use valid test certificate from .env.example
        valid_cert = """-----BEGIN CERTIFICATE-----
MIIE8TCCA9mgAwIBAgISA48pSPsqSMyRseyWkKjqrgm3MA0GCSqGSIb3DQEBCwUA
MDIxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQswCQYDVQQD
EwJSMzAeFw0yMzEyMjgxMDA5NDRaFw0yNDAzMjcxMDA5NDNaMBcxFTATBgNVBAMM
DCouYW11Z3VhLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANHp
/APp/xK+oINkRFaTtXNomrGt+T2/u5tivBD74/tTghkBe9DCob6OmX3J4YsYg5Ll
WO+66o56ad4lUKJwdp6g2hulbw/T6SgI96R91XGgvnnhyz3T06H9HKE0aDwn9JQ8
cADpdIm0cYShPEik4S1aVBL16AH1HGqYXhxlBbVLUNoWLGAFqrEzFF/ZS04WEbPt
veWRIOWoqWFqqpFmMIfFodJvrIWbCSHuHIM8VdU6m6sjhJkP73mWcIrl0Wi7IZc2
f4G8u8I+WXCatmSfE80YtAJimi5fn+kXzSGR6IV9cdpYHqx3apdWc0vTVWqqyoul
l5d/+ijAUmkkr4PSwA0CAwEAAaOCAhowggIWMA4GA1UdDwEB/wQEAwIFoDAdBgNV
HSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwDAYDVR0TAQH/BAIwADAdBgNVHQ4E
FgQUDrvkV12XMK1bOSU/t32ZwQinNc8wHwYDVR0jBBgwFoAUFC6zF7dYVsuuUAlA
5h+vnYsUwsYwVQYIKwYBBQUHAQEESTBHMCEGCCsGAQUFBzABhhVodHRwOi8vcjMu
by5sZW5jci5vcmcwIgYIKwYBBQUHMAKGFmh0dHA6Ly9yMy5pLmxlbmNyLm9yZy8w
IwYDVR0RBBwwGoIMKi5hbXVndWEuY29tggphbXVndWEuY29tMBMGA1UdIAQMMAow
CAYGZ4EMAQIBMIIBBAYKKwYBBAHWeQIEAgSB9QSB8gDwAHcASLDja9qmRzQP5WoC
+p0w6xxSActW3SyB2bu/qznYhHMAAAGMsB2tkAAABAMASDBGAiEA1BBlKNkEupcj
B5+wd1AsPkDrr0eGPxsd/pBosdFWlL0CIQD7drlb1BxF/DjDb6DPqjk4VLJuqJ68
z74p+1SpahYjRgB1ADtTd3U+LbmAToswWwb+QDtn2E/D9Me9AA0tcm/h+tQXAAAB
jLAdrZMAAAQDAEYwRAIgRi3sbBP8P6Onuf+A18ncDxbMin3xmBm7OhWw2UjEV80C
IEYpfT2myi/iYexBTEHBjVHa7qHZ5hoY69gkEImPJvPTMA0GCSqGSIb3DQEBCwUA
A4IBAQBpxyjlL9G5doUmLykjat7jpKeC6OC1dC+lZeE09aRXXp5VnuyATe3A9pPW
WiumjlnpbuZ5T43km3CQ4zBZSHv5fqnCjcopn6t2N+edFVytmyjZcJ13PSzSz5R7
CGwEyc185MntDtvzkMlXVvcV6x6SMghFb3uP138i/0eMRs8CZPVYAYKq98OopCn6
dL7AZNiJQxGQ5WkFFiuHTWz5fC/OOMIme567guxXruYHkdCyhAkoIs06pOC/p4DD
ygfSNN03BTEoQ7T16vzhtMpofkk/gXZb6CXEX5ckBjg0CM9I1Xf8BZAfbJMfdqOr
AIqjJU+SsN/cwkfCEPVkY02qfDZz
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFFjCCAv6gAwIBAgIRAJErCErPDBinU/bWLiWnX1owDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMjAwOTA0MDAwMDAw
WhcNMjUwOTE1MTYwMDAwWjAyMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNTGV0J3Mg
RW5jcnlwdDELMAkGA1UEAxMCUjMwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQC7AhUozPaglNMPEuyNVZLD+ILxmaZ6QoinXSaqtSu5xUyxr45r+XXIo9cP
R5QUVTVXjJ6oojkZ9YI8QqlObvU7wy7bjcCwXPNZOOftz2nwWgsbvsCUJCWH+jdx
sxPnHKzhm+/b5DtFUkWWqcFTzjTIUu61ru2P3mBw4qVUq7ZtDpelQDRrK9O8Zutm
NHz6a4uPVymZ+DAXXbpyb/uBxa3Shlg9F8fnCbvxK/eG3MHacV3URuPMrSXBiLxg
Z3Vms/EY96Jc5lP/Ooi2R6X/ExjqmAl3P51T+c8B5fWmcBcUr2Ok/5mzk53cU6cG
/kiFHaFpriV1uxPMUgP17VGhi9sVAgMBAAGjggEIMIIBBDAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMBMBIGA1UdEwEB/wQIMAYB
Af8CAQAwHQYDVR0OBBYEFBQusxe3WFbLrlAJQOYfr52LFMLGMB8GA1UdIwQYMBaA
FHm0WeZ7tuXkAXOACIjIGlj26ZtuMDIGCCsGAQUFBwEBBCYwJDAiBggrBgEFBQcw
AoYWaHR0cDovL3gxLmkubGVuY3Iub3JnLzAnBgNVHR8EIDAeMBygGqAYhhZodHRw
Oi8veDEuYy5sZW5jci5vcmcvMCIGA1UdIAQbMBkwCAYGZ4EMAQIBMA0GCysGAQQB
gt8TAQEBMA0GCSqGSIb3DQEBCwUAA4ICAQCFyk5HPqP3hUSFvNVneLKYY611TR6W
PTNlclQtgaDqw+34IL9fzLdwALduO/ZelN7kIJ+m74uyA+eitRY8kc607TkC53wl
ikfmZW4/RvTZ8M6UK+5UzhK8jCdLuMGYL6KvzXGRSgi3yLgjewQtCPkIVz6D2QQz
CkcheAmCJ8MqyJu5zlzyZMjAvnnAT45tRAxekrsu94sQ4egdRCnbWSDtY7kh+BIm
lJNXoB1lBMEKIq4QDUOXoRgffuDghje1WrG9ML+Hbisq/yFOGwXD9RiX8F6sw6W4
avAuvDszue5L3sz85K+EC4Y/wFVDNvZo4TYXao6Z0f+lQKc0t8DQYzk1OXVu8rp2
yJMC6alLbBfODALZvYH7n7do1AZls4I9d1P4jnkDrQoxB3UqQ9hVl3LEKQ73xF1O
yK5GhDDX8oVfGKF5u+decIsH4YaTw7mP3GFxJSqv3+0lUFJoi5Lc5da149p90Ids
hCExroL1+7mryIkXPeFM5TgO9r0rvZaBFOvV2z0gp35Z0+L4WPlbuEjN/lxPFin+
HlUjr8gRsI3qfJOQFy/9rKIJR0Y/8Omwt/8oTWgy1mdeHmmjk7j1nYsvC9JSQ6Zv
MldlTTKB3zhThV1+XWYp6rjd5JW1zbVWEkLNxE7GJThEUG3szgBVGP7pSWTUTsqX
nLRbwHOoq7hHwg==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFYDCCBEigAwIBAgIQQAF3ITfU6UK47naqPGQKtzANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTIxMDEyMDE5MTQwM1oXDTI0MDkzMDE4MTQwM1ow
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwggIiMA0GCSqGSIb3DQEB
AQUAA4ICDwAwggIKAoICAQCt6CRz9BQ385ueK1coHIe+3LffOJCMbjzmV6B493XC
ov71am72AE8o295ohmxEk7axY/0UEmu/H9LqMZshftEzPLpI9d1537O4/xLxIZpL
wYqGcWlKZmZsj348cL+tKSIG8+TA5oCu4kuPt5l+lAOf00eXfJlII1PoOK5PCm+D
LtFJV4yAdLbaL9A4jXsDcCEbdfIwPPqPrt3aY6vrFk/CjhFLfs8L6P+1dy70sntK
4EwSJQxwjQMpoOFTJOwT2e4ZvxCzSow/iaNhUd6shweU9GNx7C7ib1uYgeGJXDR5
bHbvO5BieebbpJovJsXQEOEO3tkQjhb7t/eo98flAgeYjzYIlefiN5YNNnWe+w5y
sR2bvAP5SQXYgd0FtCrWQemsAXaVCg/Y39W9Eh81LygXbNKYwagJZHduRze6zqxZ
Xmidf3LWicUGQSk+WT7dJvUkyRGnWqNMQB9GoZm1pzpRboY7nn1ypxIFeFntPlF4
FQsDj43QLwWyPntKHEtzBRL8xurgUBN8Q5N0s8p0544fAQjQMNRbcTa0B7rBMDBc
SLeCO5imfWCKoqMpgsy6vYMEG6KDA0Gh1gXxG8K28Kh8hjtGqEgqiNx2mna/H2ql
PRmP6zjzZN7IKw0KKP/32+IVQtQi0Cdd4Xn+GOdwiK1O5tmLOsbdJ1Fu/7xk9TND
TwIDAQABo4IBRjCCAUIwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMCAQYw
SwYIKwYBBQUHAQEEPzA9MDsGCCsGAQUFBzAChi9odHRwOi8vYXBwcy5pZGVudHJ1
c3QuY29tL3Jvb3RzL2RzdHJvb3RjYXgzLnA3YzAfBgNVHSMEGDAWgBTEp7Gkeyxx
+tvhS5B1/8QVYIWJEDBUBgNVHSAETTBLMAgGBmeBDAECATA/BgsrBgEEAYLfEwEB
ATAwMC4GCCsGAQUFBwIBFiJodHRwOi8vY3BzLnJvb3QteDEubGV0c2VuY3J5cHQu
b3JnMDwGA1UdHwQ1MDMwMaAvoC2GK2h0dHA6Ly9jcmwuaWRlbnRydXN0LmNvbS9E
U1RST09UQ0FYM0NSTC5jcmwwHQYDVR0OBBYEFHm0WeZ7tuXkAXOACIjIGlj26Ztu
MA0GCSqGSIb3DQEBCwUAA4IBAQAKcwBslm7/DlLQrt2M51oGrS+o44+/yQoDFVDC
5WxCu2+b9LRPwkSICHXM6webFGJueN7sJ7o5XPWioW5WlHAQU7G75K/QosMrAdSW
9MUgNTP52GE24HGNtLi1qoJFlcDyqSMo59ahy2cI2qBDLKobkx/J3vWraV0T9VuG
WCLKTVXkcGdtwlfFRjlBz4pYg1htmf5X6DYO8A4jqv2Il9DjXA6USbW1FzXSLr9O
he8Y4IWS6wY7bCkjCWDcRQJMEhg76fsO3txE+FiYruq9RUWhiF1myv4Q6W+CyBFC
Dfvp7OOGAN6dEOM4+qR9sdjoSYKEBpsr6GtPAQw4dy753ec5
-----END CERTIFICATE-----"""
        valid_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA0en8A+n/Er6gg2REVpO1c2iasa35Pb+7m2K8EPvj+1OCGQF7
0MKhvo6ZfcnhixiDkuVY77rqjnpp3iVQonB2nqDaG6VvD9PpKAj3pH3VcaC+eeHL
PdPTof0coTRoPCf0lDxwAOl0ibRxhKE8SKThLVpUEvXoAfUcapheHGUFtUtQ2hYs
YAWqsTMUX9lLThYRs+295ZEg5aipYWqqkWYwh8Wh0m+shZsJIe4cgzxV1TqbqyOE
mQ/veZZwiuXRaLshlzZ/gby7wj5ZcJq2ZJ8TzRi0AmKaLl+f6RfNIZHohX1x2lge
rHdql1ZzS9NVaqrKi6WXl3/6KMBSaSSvg9LADQIDAQABAoIBAQCYUjXxkSbqrzFC
psuAF4cfy9QVAq1NxYeZZbgaiu4QPbS1+IGkJte/szJmOMxVZuBzA8HZk8UIxoN0
E5fDh+BLk2UxkoZY8ejKiFdLIZR087PENbiJkOCNN2JDCAhrPoMX3hNYVg+erTWC
jI12GU7c3iML7yz/3qFUKGSCLjxKJKCEVD73+pRXfC4GyjPfXBiqedCrMWZbgTOx
DZo8oyIk0k818xKs0Ke1vlIWWEmpbuw0BABEdwSThhbgmpIRjYBkVVCDuYpfHe+v
KMN6gAbStWcxuIqeJ+93A09utZilnt7D6UvLhTbQhGY1Y/mqzdxAoU0j+MTxa1jX
imMBGSZxAoGBAOdRB9qkd6xJ1gD6RcmOBiQRm6FZ677WiqvL85Fm6K2wi1a7DknH
mq+nyQyH744EegGaGGilsrUdOWVHnf4hpSv66M1UUiNEWDYdtxpn+DNJkxFxRWlC
OJnXuQymNEH/E0IF7xqKKYQLsqRV6iaJg1u2Z93QBXicGPV9yvUOuO0DAoGBAOhQ
SslNK7I17BClazoJ4DZK3SbKH0qxADypdkMp8dCSxf7+ef53RUs1rpdq49/FmGnR
ZGcpQ4483lr2L7dOaL3PWQ+D5sMqanCvJ0sX3yJjdXmz7vsDF6QJN0UGcFKYdi2p
WEl222ZPX+baH0chtga7PjYfYq+pCDQ6mCMsO+mvAoGBAI3B7+FDN3/jQ/4XYltR
6VuDWu/37mxmiFceRydNfLys28eMHQaEB70sQx6l094hyi9fIyRGn4002q7BxAYw
0ktwmejzit7IDJMlhMfu/YFYzoM6+oG2Ln/BX0tsM8xaKJAmmNCX6Tdd/92MNVHm
phS3ZVHfIOs4JmeT7qRdoGDHAoGBAJJZcqOZ7/sWqR5bd09axVqukt9K2aeuFd4h
S5VIKUQiEoVvPt8luAuHR/OvrNpdmoSfGsc6YYqLofBfwvORe76Hjy2NBKTSZbeT
QAe4hCMf0PPYfKa47f2yqJTdV4lQ7rIZSrsNG246dsnxg17GR+u5rZle8EaFD9wH
Raxyw1OVAoGAakA6wO6AQeh9ZzvAiel8x4je2AnudDA6B0yb+O3XC6EpoZw+//k4
/Lo53pBurzxEFk1FHqdw+kHsuy94UPUUqWsoL4hCQG9MUpvNd9yS11FDJOydc51M
tkNkku9BXJFJy5bAVs9NxLLOs2OI+REJykbT9zBMiOkAeeFppKYP+qU=
-----END RSA PRIVATE KEY-----"""
        configs = []
        for domain in ["example1.com", "example2.com", "example3.com"]:
            cdn_config = CdnConfig(
                domain_names=[domain],
                cert=valid_cert,
                cert_private_key=valid_key,
                region="cn-hangzhou",
            )
            app_config = AppConfig(
                service_type="cdn",
                cloud_provider="alibaba",
                auth_method="access_key",
                credentials=Credentials(
                    access_key_id="test_key",
                    access_key_secret="test_secret",
                ),
                cdn_config=cdn_config,
                webhook_config=webhook_config,
            )
            configs.append(app_config)

        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_fingerprint.return_value = (
            None  # No current cert, will proceed with renewal
        )
        # Two succeed, one fails
        mock_do_renew.side_effect = [True, False, True]

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create renewers for each config
        renewers = [
            CdnCertRenewerStrategy(config, config.cdn_config.domain_names[0])
            for config in configs
        ]

        # Create composite renewer
        composite = CompositeCertRenewer(renewers)

        # Execute batch renewal
        result = composite.renew()

        # Verify batch had one failure
        assert result is False

        # Wait a bit for async webhook calls
        time.sleep(0.1)

        # Each renewer sends 2 webhooks (started + result) + 1 batch summary
        expected_calls = (3 * 2) + 1  # 3 renewers * 2 events each + 1 batch summary
        assert mock_client.deliver.call_count == expected_calls

        # Check batch summary webhook (last call)
        batch_call_args = mock_client.deliver.call_args_list[-1]
        batch_payload = batch_call_args[0][1]
        assert batch_payload["event_type"] == "batch_completed"
        assert batch_payload["metadata"]["total_resources"] == 3
        assert batch_payload["metadata"]["successful_resources"] == 2
        assert batch_payload["metadata"]["failed_resources"] == 1
        assert batch_payload["result"]["status"] == "failure"
        assert "2/3 succeeded" in batch_payload["result"]["message"]

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.base.BaseCertRenewer.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    def test_webhook_disabled_no_calls(
        self,
        mock_do_renew,
        mock_get_fingerprint,
        mock_is_cert_valid,
        mock_client_class,
        cdn_config,
    ):
        """Test that no webhooks are sent when webhook is not configured"""
        # Create config without webhook
        app_config = AppConfig(
            service_type="cdn",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=Credentials(
                access_key_id="test_key",
                access_key_secret="test_secret",
            ),
            cdn_config=cdn_config,
            webhook_config=None,  # No webhook config
        )

        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_fingerprint.return_value = (
            None  # No current cert, will proceed with renewal
        )
        mock_do_renew.return_value = True

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify renewal succeeded
        assert result is True

        # Verify no webhook client was created or used
        mock_client_class.assert_not_called()

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.cert_renewer.cdn_renewer.is_cert_valid")
    @patch(
        "cloud_cert_renewer.cert_renewer.base.BaseCertRenewer.get_current_cert_fingerprint"
    )
    @patch(
        "cloud_cert_renewer.cert_renewer.cdn_renewer.CdnCertRenewerStrategy._do_renew"
    )
    def test_webhook_filtered_events(
        self,
        mock_do_renew,
        mock_get_fingerprint,
        mock_is_cert_valid,
        mock_client_class,
        cdn_config,
    ):
        """Test that only enabled webhook events are sent"""
        # Create config with filtered webhook events
        webhook_config = WebhookConfig(
            url="https://example.com/webhook",
            enabled_events={"renewal_success"},  # Only success events
        )
        app_config = AppConfig(
            service_type="cdn",
            cloud_provider="alibaba",
            auth_method="access_key",
            credentials=Credentials(
                access_key_id="test_key",
                access_key_secret="test_secret",
            ),
            cdn_config=cdn_config,
            webhook_config=webhook_config,
        )

        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_fingerprint.return_value = (
            None  # No current cert, will proceed with renewal
        )
        mock_do_renew.return_value = True

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        # Create CDN renewer
        renewer = CdnCertRenewerStrategy(app_config, "example.com")

        # Execute renewal
        result = renewer.renew()

        # Verify renewal succeeded
        assert result is True

        # Wait a bit for async webhook calls
        time.sleep(0.1)

        # Only renewal_success should be sent (not renewal_started)
        assert mock_client.deliver.call_count == 1

        # Check the single call is for success
        call_args = mock_client.deliver.call_args_list[0]
        payload = call_args[0][1]
        assert payload["event_type"] == "renewal_success"
