# coding: utf-8
"""Tests exceptions."""
import pytest
from dio_chacon_wifi_api.exceptions import DIOChaconAPIError
from dio_chacon_wifi_api.exceptions import DIOChaconInvalidAuthError


def test_exceptions() -> None:

    with pytest.raises(DIOChaconAPIError):
        raise DIOChaconAPIError("Dumb test coverage")

    with pytest.raises(DIOChaconInvalidAuthError):
        raise DIOChaconInvalidAuthError("Dumb 2")
