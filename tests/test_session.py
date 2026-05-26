# coding: utf-8
"""Tests session.py. DIOChaconClientSession class."""
import asyncio
import logging
from typing import Any

import pytest
from aiohttp_fake_server_utils import MOCK_PORT
from aiohttp_fake_server_utils import run_fake_http_server
from dio_chacon_wifi_api.session import DIOChaconClientSession

_LOGGER = logging.getLogger(__name__)

USERNAME = 'toto@toto.com'
PASSWORD = 'DUMMY_PASS'
SERVICE_NAME = "test_client"


@pytest.mark.asyncio
async def test_session(aiohttp_server) -> None:
    """Test generic for session."""

    recording_queue: asyncio.Queue = asyncio.Queue()
    message_queue: asyncio.Queue = asyncio.Queue()
    await run_fake_http_server(aiohttp_server, recording_queue)

    _LOGGER.debug("Launching test session...")

    def message_callback(data: Any) -> None:
        _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
        _LOGGER.info(data)
        _LOGGER.info("******** CALLBACK MESSAGE DONE *******")
        message_queue.put_nowait(data)

    session = DIOChaconClientSession(USERNAME, PASSWORD, SERVICE_NAME, message_callback)
    session._set_server_urls(f"ws://localhost:{MOCK_PORT}/ws")

    await session.ws_connect()

    message = await asyncio.wait_for(message_queue.get(), 2)
    assert message["name"] == 'connection'
    assert message["action"] == 'success'
    message_queue.task_done()

    await session.disconnect()
