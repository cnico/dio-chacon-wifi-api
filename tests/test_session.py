# coding: utf-8
"""Tests session.py. DIOChaconClientSession class."""
import logging
from typing import Any

import pytest
from aioresponses import aioresponses
from dio_chacon_wifi_api.const import DIOCHACON_AUTH_URL
from dio_chacon_wifi_api.const import DIOCHACON_WS_URL
from dio_chacon_wifi_api.session import DIOChaconClientSession

_LOGGER = logging.getLogger(__name__)

USERNAME = 'toto@toto.com'
PASSWORD = 'DUMMY_PASS'
INSTALLATION_ID = "NOID"


def log_callback(data: Any) -> None:
    _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
    _LOGGER.info(data)
    _LOGGER.info("******** CALLBACK MESSAGE DONE *******")


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest.mark.asyncio
async def test_session(mock_aioresponse) -> None:
    """Test generic for session."""

    mock_aioresponse.post(DIOCHACON_AUTH_URL, body='{"status":200,"data":{"sessionToken":"r:myfakesessionToken"}}')

    session = DIOChaconClientSession(USERNAME, PASSWORD, INSTALLATION_ID, log_callback)
    session._set_server_urls(DIOCHACON_AUTH_URL, DIOCHACON_WS_URL)

    await session.login()

    mock_aioresponse.assert_called_once()
    mock_aioresponse.assert_called_with(
        url=DIOCHACON_AUTH_URL,
        method="POST",
        data='{"email": "toto@toto.com", "password": "DUMMY_PASS", "installationId": "NOID"}',
        headers={'Content-Type': 'application/json', 'Cache-Control': 'no-cache'},
    )

    await session.disconnect()
