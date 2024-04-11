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
MY_LIGHT_ID = os.environ.get('DIO_SHUTTER_ID_TEST_LIGHT')

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
async def test_integration_simple() -> None:
    """Connect then lists all the devices."""

    assert USERNAME is not None, "Please set env var before running integration tests !"

    def log_callback(data: Any) -> None:
        _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
        _LOGGER.info(data)
        _LOGGER.info("******** CALLBACK MESSAGE DONE *******")

    # Init client
    client = DIOChaconAPIClient(USERNAME, PASSWORD, callback_device_state=log_callback)

    user_id = await client.get_user_id()
    _LOGGER.info(f"User Id retrieved : {user_id}")

    list_devices = await client.search_all_devices(device_type_to_search=DeviceTypeEnum.LIGHT, with_state=True)
    _LOGGER.info(f"Devices found : {list_devices}")

    my_device = list_devices[MY_LIGHT_ID]
    _LOGGER.info(f"My device found {MY_LIGHT_ID} : {my_device}")
    assert my_device['name'] == 'Lumiere Test'
    assert my_device['type'] == DeviceTypeEnum.LIGHT

    # get shutter position
    list_details = await client.get_status_details([MY_LIGHT_ID])
    _LOGGER.info(f"Details found : {list_details}")

    _LOGGER.info("---------- Switch On ---------")
    await client.switch_light(MY_LIGHT_ID, True)

    await asyncio.sleep(5)

    list_details = await client.get_status_details([MY_LIGHT_ID])
    _LOGGER.info(f"Details after swith on: {list_details}")

    await client.switch_light(MY_LIGHT_ID, False)

    await asyncio.sleep(5)

    list_details = await client.get_status_details([MY_LIGHT_ID])
    _LOGGER.info(f"Details after swith off: {list_details}")

    _LOGGER.info("End of integration tests : disconnecting...")

    await client.disconnect()
