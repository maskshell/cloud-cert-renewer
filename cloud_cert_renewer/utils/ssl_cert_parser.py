import re
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes


def parse_cert_info(cert_content: str) -> tuple[list[str], datetime]:
    """
    Parse cert info from cert content, return domain name list and expire date and time.
    For certificate chains, only the first certificate (server certificate) is parsed.
    :param cert_content: cert content (may contain certificate chain)
    :return: domain name list and expire datetime (UTC-aware)
    """
    # For certificate chains, only parse the first certificate
    # (server certificate)
    # load_pem_x509_certificate will automatically handle this,
    # only loading the first certificate
    cert = x509.load_pem_x509_certificate(cert_content.encode(), default_backend())

    # Prefer UTC-aware datetime to avoid deprecated naive datetime properties.
    not_valid_after_utc = getattr(cert, "not_valid_after_utc", None)
    if not_valid_after_utc is not None:
        cert_expire_date = not_valid_after_utc
    else:
        # Backward compatible fallback for older cryptography versions.
        cert_expire_date = cert.not_valid_after.replace(tzinfo=timezone.utc)

    # Get domain name list (from Subject and SAN extension)
    cert_domain_name_list = []

    # Get domain name from Subject CN
    for domain_name in cert.subject.get_attributes_for_oid(
        x509.oid.NameOID.COMMON_NAME
    ):
        cert_domain_name_list.append(domain_name.value)

    # Get domain name from SAN (Subject Alternative Name) extension
    try:
        san_ext = cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        for name in san_ext.value:
            if isinstance(name, x509.DNSName):
                cert_domain_name_list.append(name.value)
    except x509.ExtensionNotFound:
        # SAN extension does not exist, only use CN
        pass

    return cert_domain_name_list, cert_expire_date


def is_domain_name_match(domain_name: str, domain_name_list: list[str]) -> bool:
    """
    Check a specified domain name whether in a domain name list.
    The domain name list may contain a wildcard domain name.
    :param domain_name: specified domain name to check
    :param domain_name_list: domain name list contains in ssl cert
    :return: True if specified domain name in the list, otherwise False.
    """
    for domain_name_item in domain_name_list:
        if domain_name_item == "*":
            return True

        # RFC 6125-style wildcard: "*.example.com" matches exactly one label.
        if domain_name_item.startswith("*."):
            suffix = domain_name_item[2:]
            if domain_name == suffix:
                continue
            if domain_name.endswith("." + suffix):
                prefix = domain_name[: -(len(suffix) + 1)]
                if prefix and "." not in prefix:
                    return True
            continue

        if domain_name_item.startswith("*"):
            # Fallback for non-standard wildcard patterns.
            if re.match(
                r"^" + domain_name_item.replace(".", r"\.").replace("*", r".*") + "$",
                domain_name,
            ):
                return True
            continue

        # Exact match
        if domain_name_item == domain_name:
            return True
    return False


def is_cert_valid(cert_content: str, domain_name: str) -> bool:
    """
    Parse a cert, and check whether a specified domain name in the cert.
    If the specified domain name in the cert, and the cert expire date is
    later than current date, then return True, otherwise return False.
    :param cert_content: cert content
    :param domain_name: specified domain name
    :return: True if specified domain name in the cert, and the cert expire
    date is later than current date, otherwise return False.
    """
    cert_domain_name_list, cert_expire_date = parse_cert_info(cert_content)
    if not is_domain_name_match(domain_name, cert_domain_name_list):
        return False

    return cert_expire_date > datetime.now(timezone.utc)


def get_cert_fingerprint_sha256(cert_content: str) -> str:
    """
    Calculate SHA256 fingerprint of the certificate.
    For certificate chains, only the first certificate (server certificate) is used.
    :param cert_content: cert content (may contain certificate chain)
    :return: SHA256 fingerprint in colon-separated format (uppercase)
    """
    cert = x509.load_pem_x509_certificate(cert_content.encode(), default_backend())
    fingerprint = cert.fingerprint(hashes.SHA256())
    return ":".join(
        fingerprint.hex()[i : i + 2].upper()
        for i in range(0, len(fingerprint.hex()), 2)
    )


def get_cert_fingerprint_sha1(cert_content: str) -> str:
    """
    Calculate SHA1 fingerprint of the certificate.
    For certificate chains, only the first certificate (server certificate) is used.
    :param cert_content: cert content (may contain certificate chain)
    :return: SHA1 fingerprint in colon-separated format (lowercase)
    """
    cert = x509.load_pem_x509_certificate(cert_content.encode(), default_backend())
    fingerprint = cert.fingerprint(hashes.SHA1())
    return ":".join(
        fingerprint.hex()[i : i + 2].lower()
        for i in range(0, len(fingerprint.hex()), 2)
    )


def normalize_hex_fingerprint(fingerprint: str) -> str:
    """Normalize a hex fingerprint string to colon-separated lowercase bytes.

    This is useful when comparing API-returned fingerprints that may differ in
    casing or separators (e.g., "AA:BB" vs "aa-bb" vs "AABB").
    """

    raw = "".join(ch for ch in fingerprint.strip() if ch.lower() in "0123456789abcdef")
    if not raw or len(raw) % 2 != 0:
        return fingerprint.strip().lower()
    raw = raw.lower()
    return ":".join(raw[i : i + 2] for i in range(0, len(raw), 2))
