from datetime import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from typing import List
import re


def parse_cert_info(cert_content: str) -> (List[str], str):
    """
    Parse cert info from cert content, return domain name list and expire date and time.
    For certificate chains, only the first certificate (server certificate) is parsed.
    :param cert_content: cert content (may contain certificate chain)
    :return: domain name list and expire date
    """
    # 对于证书链，只解析第一个证书（服务器证书）
    # load_pem_x509_certificate 会自动处理，只加载第一个证书
    cert = x509.load_pem_x509_certificate(cert_content.encode(), default_backend())
    cert_expire_date = cert.not_valid_after.strftime("%Y-%m-%d %H:%M:%S")

    # 获取域名列表（从 Subject 和 SAN 扩展中）
    cert_domain_name_list = []

    # 从 Subject CN 获取域名
    for domain_name in cert.subject.get_attributes_for_oid(
        x509.oid.NameOID.COMMON_NAME
    ):
        cert_domain_name_list.append(domain_name.value)

    # 从 SAN (Subject Alternative Name) 扩展获取域名
    try:
        san_ext = cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        for name in san_ext.value:
            if isinstance(name, x509.DNSName):
                cert_domain_name_list.append(name.value)
    except x509.ExtensionNotFound:
        # SAN 扩展不存在，只使用 CN
        pass

    return cert_domain_name_list, cert_expire_date


def is_domain_name_match(domain_name: str, domain_name_list: List[str]) -> bool:
    """
    Check a specified domain name whether in a domain name list.
    The domain name list may contain a wildcard domain name.
    :param domain_name: specified domain name to check
    :param domain_name_list: domain name list contains in ssl cert
    :return: True if specified domain name in the list, otherwise False.
    """
    for domain_name_item in domain_name_list:
        if domain_name_item.startswith("*"):
            # If the domain name item in the list is a wildcard domain name, use regular expression to check.
            if re.match(
                r"^" + domain_name_item.replace(".", r"\.").replace("*", r".*") + "$",
                domain_name,
            ):
                return True
        else:
            # If the domain name item in the list is not a wildcard domain name, just check it.
            if domain_name_item == domain_name:
                return True
    return False


def is_cert_valid(cert_content: str, domain_name: str) -> bool:
    """
    Parse a cert, and check whether a specified domain name in the cert.
    If the specified domain name in the cert, and the cert expire date is later than current date,
    then return True, otherwise return False.
    :param cert_content: cert content
    :param domain_name: specified domain name
    :return: True if specified domain name in the cert, and the cert expire date is later than current date,
    otherwise return False.
    """
    cert_domain_name_list, cert_expire_date = parse_cert_info(cert_content)
    if is_domain_name_match(domain_name, cert_domain_name_list):
        # If the specified domain name in the cert, and the cert expire date is later than current date,
        # then return True, otherwise return False.
        if cert_expire_date > datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            return True
    return False
