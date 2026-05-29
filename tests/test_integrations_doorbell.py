# coding: utf-8
"""Integration tests for DIO Chacon wifi api."""
import asyncio
import logging
import os
from typing import Any

import pytest
from dio_chacon_wifi_api import DIOChaconAPIClient
from dio_chacon_wifi_api.const import DeviceTypeEnum

# Enter correct real values here for the tests to complete successfully with real Server calls.

USERNAME = os.environ.get('DIO_USERNAME')
PASSWORD = os.environ.get('DIO_PASSWORD')
SESSION_TOKEN = os.environ.get('DIO_SESSION_TOKEN')
MY_DOORBELL_ID = os.environ.get('DIO_DOORBELL_ID_TEST')

RING_WAIT_TIMEOUT_SECONDS = 60

logging.basicConfig(level=logging.DEBUG)

_LOGGER = logging.getLogger(__name__)

if os.environ.get('PYDBG', None):
    # This code will block execution until you run your Python: Remote Attach
    port = 5678
    host = 'localhost'
    print(f"Blocking for remote attach for vscode {host} {port}")
    import debugpy

    debugpy.listen((host, port))
    debugpy.wait_for_client()


@pytest.mark.skip("Not an automated test but an example of usage with real values.")
@pytest.mark.asyncio
async def test_integration_doorbell() -> None:
    """Connect, list the doorbell, then wait for a manual ring and assert ring and image features."""

    assert SESSION_TOKEN or USERNAME, "Please set env var before running integration tests !"

    global_ring_events: asyncio.Queue = asyncio.Queue()
    per_device_ring_events: asyncio.Queue = asyncio.Queue()

    def global_callback(data: Any) -> None:
        _LOGGER.info("******** GLOBAL CALLBACK MESSAGE RECEIVED *******")
        _LOGGER.info(data)
        global_ring_events.put_nowait(data)
        _LOGGER.info("******** GLOBAL CALLBACK MESSAGE DONE *******")

    def per_device_callback(data: Any) -> None:
        _LOGGER.info("******** PER DEVICE CALLBACK MESSAGE RECEIVED *******")
        _LOGGER.info(data)
        per_device_ring_events.put_nowait(data)
        _LOGGER.info("******** PER DEVICE CALLBACK MESSAGE DONE *******")

    if SESSION_TOKEN:
        client = DIOChaconAPIClient(session_token=SESSION_TOKEN, callback_device_state=global_callback)
    else:
        client = DIOChaconAPIClient(USERNAME, PASSWORD, callback_device_state=global_callback)
    client.set_callback_device_state_by_device(MY_DOORBELL_ID, per_device_callback)

    user_id = await client.get_user_id()
    _LOGGER.info(f"User Id retrieved : {user_id}")

    list_devices = await client.search_all_devices(device_type_to_search=[DeviceTypeEnum.DOORBELL], with_state=True)
    _LOGGER.info(f"Devices found : {list_devices}")

    my_device = list_devices[MY_DOORBELL_ID]
    _LOGGER.info(f"My device found {MY_DOORBELL_ID} : {my_device}")
    assert my_device['type'] == DeviceTypeEnum.DOORBELL.value
    assert 'last_event_type' in my_device
    assert 'last_event_timestamp' in my_device

    list_details = await client.get_status_details([MY_DOORBELL_ID])
    _LOGGER.info(f"Details found : {list_details}")

    _LOGGER.info(
        "---------- Please ring the doorbell now (timeout %ss). Covers 'ring' AND 'image' features. ---------",
        RING_WAIT_TIMEOUT_SECONDS,
    )

    global_event = await asyncio.wait_for(global_ring_events.get(), RING_WAIT_TIMEOUT_SECONDS)
    _LOGGER.info(f"Global ring callback payload : {global_event}")
    assert global_event['id'] == MY_DOORBELL_ID
    assert global_event['type'] == DeviceTypeEnum.DOORBELL.value
    assert global_event['connected']
    assert global_event['last_event_type'] == 'ring'
    assert isinstance(global_event['last_event_timestamp'], str)
    assert global_event['last_event_image'].startswith('https://')

    per_device_event = await asyncio.wait_for(per_device_ring_events.get(), RING_WAIT_TIMEOUT_SECONDS)
    _LOGGER.info(f"Per device ring callback payload : {per_device_event}")
    assert per_device_event['id'] == MY_DOORBELL_ID
    assert per_device_event['last_event_type'] == 'ring'
    assert per_device_event['last_event_image'].startswith('https://')

    _LOGGER.info("End of integration tests : disconnecting...")

    await client.disconnect()
