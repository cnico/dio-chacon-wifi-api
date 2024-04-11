# coding: utf-8
"""Tests client.py. DIOChaconAPIClient class."""
import asyncio
import logging
from typing import Any

import aiohttp
import pytest
from aiohttp_fake_server_utils import MOCK_PORT
from aiohttp_fake_server_utils import run_fake_http_server
from dio_chacon_wifi_api.client import DIOChaconAPIClient

_LOGGER = logging.getLogger(__name__)

USERNAME = 'toto@toto.com'
PASSWORD = 'DUMMY_PASS'
INSTALLATION_ID = "NOID"


def log_callback(data: Any) -> None:
    _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
    _LOGGER.info(data)
    _LOGGER.info("******** CALLBACK MESSAGE DONE *******")


@pytest.mark.asyncio
async def test_client(aiohttp_server) -> None:
    """Test generic for client."""

    recording_queue: asyncio.Queue = asyncio.Queue()
    await run_fake_http_server(aiohttp_server, recording_queue)

    _LOGGER.debug("Launching test client...")

    client = DIOChaconAPIClient(USERNAME, PASSWORD, INSTALLATION_ID, log_callback)
    client._set_server_urls(f"http://localhost:{MOCK_PORT}/api/session/login", f"ws://localhost:{MOCK_PORT}/ws")

    await client.get_user_id()

    effective_request: aiohttp.web.Request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Result : %s", effective_request)
    assert effective_request["method"] == "POST"
    assert effective_request["rel_url"] == "/api/session/login"
    assert effective_request["body"] == '{"email": "toto@toto.com", "password": "DUMMY_PASS", "installationId": "NOID"}'

    await client.disconnect()
