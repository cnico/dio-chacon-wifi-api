"""Exceptions for DIOChaconAPIClient."""


class DIOChaconAPIError(Exception):
    """Error from this api."""

    def __init__(self, *args) -> None:
        Exception.__init__(self, *args)
