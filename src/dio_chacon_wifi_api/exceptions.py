"""Exceptions for DIOChaconAPIClient."""
from typing import Any


class DIOChaconAPIError(Exception):
    """Error from this api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception.

        Args:
            args: the message or root cause of the error
        """
        Exception.__init__(self, *args)
