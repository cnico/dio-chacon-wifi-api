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
from dio_chacon_wifi_api.exceptions import DIOChaconInvalidAuthError

_LOGGER = logging.getLogger(__name__)

USERNAME = 'toto@toto.com'
PASSWORD = 'DUMMY_PASS'
SERVICE_NAME = "test_client"

INVALID_PASSWORD = 'PASS_INVALID_AUTH'


def log_callback(data: Any) -> None:
    _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
    _LOGGER.info(data)
    assert data["id"]
    _LOGGER.info("******** CALLBACK MESSAGE DONE *******")


@pytest.mark.asyncio
async def test_client_invalid_auth(aiohttp_server) -> None:
    """Test invalid auth exception for client giving bad credential."""

    recording_queue: asyncio.Queue = asyncio.Queue()
    await run_fake_http_server(aiohttp_server, recording_queue)

    _LOGGER.debug("Launching test client...")

    with pytest.raises(DIOChaconInvalidAuthError) as excinfo:
        client = DIOChaconAPIClient(USERNAME, INVALID_PASSWORD, SERVICE_NAME)
        client.set_callback_device_state(log_callback)
        client._set_server_urls(f"ws://localhost:{MOCK_PORT}/ws")
        await client.get_user_id()

    assert str(excinfo.value) == "Invalid username/password."

    _LOGGER.debug("Invalid auth test OK. Disconnecting...")

    await client.disconnect()


@pytest.mark.asyncio
async def test_client(aiohttp_server) -> None:
    """Test generic for client."""

    recording_queue: asyncio.Queue = asyncio.Queue()
    await run_fake_http_server(aiohttp_server, recording_queue)

    _LOGGER.debug("Launching test client...")

    client = DIOChaconAPIClient(USERNAME, PASSWORD, SERVICE_NAME)
    client.set_callback_device_state(log_callback)
    client._set_server_urls(f"ws://localhost:{MOCK_PORT}/ws")

    # Test get_user_id
    effective_response = await client.get_user_id()
    _LOGGER.debug("Assertion queue size = %s", recording_queue.qsize())
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
    assert effective_request["parameters"] == {
        'devices': ['L4HActuator_idmock1', 'L4HActuator_idmock2', 'Tuya_idmock4']
    }
    assert effective_request["id"] == 3
    recording_queue.task_done()

    assert len(effective_response) == 3
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
    assert effective_response["Tuya_idmock4"]["id"] == "Tuya_idmock4"
    assert effective_response["Tuya_idmock4"]["name"] == "Doorbell mock 4"
    assert effective_response["Tuya_idmock4"]["type"] == "DOORBELL"
    assert effective_response["Tuya_idmock4"]["model"] == "DIOVDP-B03_Wifi: 1.1.2, MCU: 1.1.2"
    assert effective_response["Tuya_idmock4"]["connected"]  # == True
    assert effective_response["Tuya_idmock4"]["last_event_type"] == "ring"
    assert effective_response["Tuya_idmock4"]["last_event_timestamp"] == "2026-05-22T08:20:08.667Z"
    assert effective_response["Tuya_idmock4"]["last_event_image"] == "https://mock.example.com/ring.jpeg"

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


def test_doorbell_ring_callback() -> None:
    """The doorbell ring event pushed by the server is delivered through the device callback."""

    received_events: list = []
    client = DIOChaconAPIClient(USERNAME, PASSWORD, SERVICE_NAME)
    client._device_types["Tuya_idmock4"] = "DOORBELL"
    client.set_callback_device_state(received_events.append)

    ring_push = {
        "name": "deviceState",
        "action": "update",
        "data": {
            "di": "Tuya_idmock4",
            "rc": 1,
            "links": [
                {
                    "rt": "gw.r.lastEvent",
                    "href": "lastEvent",
                    "type": "ring",
                    "ts": "2026-05-22T10:21:45.714Z",
                    "data": {"reason": None, "image": "https://mock.example.com/ring.jpeg"},
                }
            ],
        },
    }
    client._message_received_callback(ring_push)

    assert len(received_events) == 1
    event = received_events[0]
    assert event["id"] == "Tuya_idmock4"
    assert event["type"] == "DOORBELL"
    assert event["connected"]
    assert event["last_event_type"] == "ring"
    assert event["last_event_image"] == "https://mock.example.com/ring.jpeg"

    unsafe_push = {
        "name": "deviceState",
        "action": "update",
        "data": {
            "di": "Tuya_idmock4",
            "rc": 1,
            "links": [
                {
                    "rt": "gw.r.lastEvent",
                    "href": "lastEvent",
                    "type": "ring",
                    "ts": "2026-05-22T10:22:00.000Z",
                    "data": {"reason": None, "image": "javascript:alert(1)"},
                }
            ],
        },
    }
    client._message_received_callback(unsafe_push)

    assert "last_event_image" not in received_events[1]
    assert received_events[1]["last_event_type"] == "ring"
    assert received_events[1]["last_event_timestamp"] == "2026-05-22T10:22:00.000Z"

    no_image_push = {
        "name": "deviceState",
        "action": "update",
        "data": {
            "di": "Tuya_idmock4",
            "rc": 1,
            "links": [
                {
                    "rt": "gw.r.lastEvent",
                    "href": "lastEvent",
                    "type": "ring",
                    "ts": "2026-05-22T10:23:00.000Z",
                    "data": {"reason": None},
                }
            ],
        },
    }
    client._message_received_callback(no_image_push)

    assert "last_event_image" not in received_events[2]
    assert received_events[2]["last_event_type"] == "ring"
    assert received_events[2]["last_event_timestamp"] == "2026-05-22T10:23:00.000Z"

    userinfo_push = {
        "name": "deviceState",
        "action": "update",
        "data": {
            "di": "Tuya_idmock4",
            "rc": 1,
            "links": [
                {
                    "rt": "gw.r.lastEvent",
                    "href": "lastEvent",
                    "type": "ring",
                    "ts": "2026-05-22T10:24:00.000Z",
                    "data": {"reason": None, "image": "https://user:secret@mock.example.com/ring.jpeg"},
                }
            ],
        },
    }
    client._message_received_callback(userinfo_push)

    assert "last_event_image" not in received_events[3]
    assert received_events[3]["last_event_type"] == "ring"
