"""Exceptions for DIOChacon API."""


class DIOChaconAPIError(Exception):
    """Error from this api."""

    def __init__(self, *args) -> None:
        Exception.__init__(self, *args)


class DIOChaconInvalidAuthError(Exception):
    """Invalid auth detected"""

    def __init__(self, *args) -> None:
        Exception.__init__(self, *args)
