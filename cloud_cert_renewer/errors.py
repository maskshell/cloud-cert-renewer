class CloudApiError(RuntimeError):
    """Cloud API call failed."""


class UnsupportedCloudProviderError(ValueError):
    """Unsupported cloud provider name."""


class UnsupportedServiceTypeError(ValueError):
    """Unsupported service type."""
