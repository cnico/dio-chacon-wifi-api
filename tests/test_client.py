# coding: utf-8
"""Tests client.py. DIOChaconAPIClient class."""
import asyncio
import logging
from typing import Any

import pytest
from aiohttp_fake_server_utils import MOCK_PORT
from aiohttp_fake_server_utils import run_fake_http_server
from dio_chacon_wifi_api.client import DIOChaconAPIClient
from dio_chacon_wifi_api.const import ShutterMoveEnum

_LOGGER = logging.getLogger(__name__)

USERNAME = 'toto@toto.com'
PASSWORD = 'DUMMY_PASS'
INSTALLATION_ID = "NOID"


def log_callback(data: Any) -> None:
    _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
    _LOGGER.info(data)
    assert data["id"]
    _LOGGER.info("******** CALLBACK MESSAGE DONE *******")


@pytest.mark.asyncio
async def test_client(aiohttp_server) -> None:
    """Test generic for client."""

    recording_queue: asyncio.Queue = asyncio.Queue()
    await run_fake_http_server(aiohttp_server, recording_queue)

    _LOGGER.debug("Launching test client...")

    client = DIOChaconAPIClient(USERNAME, PASSWORD, INSTALLATION_ID)
    client.set_callback_device_state(log_callback)
    client._set_server_urls(f"http://localhost:{MOCK_PORT}/api/session/login", f"ws://localhost:{MOCK_PORT}/ws")

    # Test get_user_id
    effective_response = await client.get_user_id()
    _LOGGER.debug("Assertion queue size = %s", recording_queue.qsize())
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Request : %s .Response : %s", effective_request, effective_response)
    assert effective_request["protocol"] == "HTTP"
    assert effective_request["method"] == "POST"
    assert effective_request["rel_url"] == "/api/session/login"
    assert effective_request["body"] == '{"email": "toto@toto.com", "password": "DUMMY_PASS", "installationId": "NOID"}'
    recording_queue.task_done()
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "GET"
    assert effective_request["path"] == "/user"
    assert effective_request["parameters"] == {}
    assert effective_request["id"] == 1
    assert effective_response == "mocked-user-id"
    recording_queue.task_done()

    # Test search_all_devices
    effective_response = await client.search_all_devices(with_state=True)
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Request : %s .Response : %s", effective_request, effective_response)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "GET"
    assert effective_request["path"] == "/device"
    assert effective_request["parameters"] == {}
    assert effective_request["id"] == 2
    recording_queue.task_done()

    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Intermediairay WS Request : %s", effective_request)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "POST"
    assert effective_request["path"] == "/device/states"
    assert effective_request["parameters"] == {'devices': ['L4HActuator_idmock1', 'L4HActuator_idmock2']}
    assert effective_request["id"] == 3
    recording_queue.task_done()

    assert len(effective_response) == 2
    assert effective_response["L4HActuator_idmock1"]["id"] == "L4HActuator_idmock1"
    assert effective_response["L4HActuator_idmock1"]["name"] == "Shutter mock 1"
    assert effective_response["L4HActuator_idmock1"]["type"] == "SHUTTER"
    assert effective_response["L4HActuator_idmock1"]["model"] == "CERSwd-3B_1.0.6"
    assert effective_response["L4HActuator_idmock1"]["connected"]  # == True
    assert effective_response["L4HActuator_idmock1"]["openlevel"] == 75
    assert effective_response["L4HActuator_idmock1"]["movement"] == "stop"
    assert effective_response["L4HActuator_idmock2"]["id"] == "L4HActuator_idmock2"
    assert effective_response["L4HActuator_idmock2"]["name"] == "Shutter mock 2"
    assert effective_response["L4HActuator_idmock2"]["type"] == "SWITCH_LIGHT"
    assert effective_response["L4HActuator_idmock2"]["model"] == "CERNwd-3B_1.0.4"
    assert effective_response["L4HActuator_idmock2"]["connected"]  # == True
    assert not effective_response["L4HActuator_idmock2"]["is_on"]  # == False
    # Device 3 is unknown so not in the response since it is filtered by the client.

    # Test move_shutter_direction
    await client.move_shutter_direction(shutter_id="L4HActuator_idmock1", direction=ShutterMoveEnum.DOWN)
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Request : %s", effective_request)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "POST"
    assert effective_request["path"] == "/device/L4HActuator_idmock1/action/mvtlinear"
    assert effective_request["parameters"] == {'movement': "down"}
    assert effective_request["id"] == 4
    recording_queue.task_done()
    # Returns is also done via a callback

    # Test move_shutter_percentage
    await client.move_shutter_percentage(shutter_id="L4HActuator_idmock1", openlevel=31)
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Request : %s", effective_request)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "POST"
    assert effective_request["path"] == "/device/L4HActuator_idmock1/action/openlevel"
    assert effective_request["parameters"] == {'openLevel': 31}
    assert effective_request["id"] == 5
    recording_queue.task_done()
    # Returns is also done via a callback

    # Test switch_switch
    await client.switch_switch(switch_id="L4HActuator_idmock2", set_on=True)
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Request : %s", effective_request)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "POST"
    assert effective_request["path"] == "/device/L4HActuator_idmock2/action/switch"
    assert effective_request["parameters"] == {'value': 1}
    assert effective_request["id"] == 6
    recording_queue.task_done()
    # Returns is also done via a callback

    # Explicitly awaits that the callbacks are executed by the fake server before disconnecting.
    _LOGGER.debug("Waiting for callbacks executions...")
    await asyncio.sleep(0.500)

    await client.disconnect()
    effective_request = await asyncio.wait_for(recording_queue.get(), 2)
    _LOGGER.debug("Intermediairay WS Request : %s", effective_request)
    assert effective_request["protocol"] == "WS"
    assert effective_request["method"] == "POST"
    assert effective_request["path"] == "/session/logout"
    assert effective_request["parameters"] == {}
    assert effective_request["id"] == 7
