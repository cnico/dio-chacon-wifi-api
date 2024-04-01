# coding: utf-8
"""Integration tests for DIO Chacon wifi api."""
import asyncio
import logging
import os
from typing import Any

import pytest
from dio_chacon_wifi_api import DIOChaconAPIClient
from dio_chacon_wifi_api.const import DeviceTypeEnum
from dio_chacon_wifi_api.const import ShutterMoveEnum

# Enter correct real values here for the tests to complete successfully with real Server calls.

USERNAME = os.environ.get('DIO_USERNAME')
PASSWORD = os.environ.get('DIO_PASSWORD')
MY_SHUTTER_ID = os.environ.get('DIO_SHUTTER_ID_TEST')

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

    def log_callback(data: Any) -> None:
        _LOGGER.info("******** CALLBACK MESSAGE RECEIVED *******")
        _LOGGER.info(data)
        _LOGGER.info("******** CALLBACK MESSAGE DONE *******")

    # Init client
    client = DIOChaconAPIClient(USERNAME, PASSWORD, callback_device_state=log_callback)

    user_id = await client.get_user_id()
    _LOGGER.info(f"User Id retrieved : {user_id}")

    list_devices = await client.search_all_devices(device_type_to_search=DeviceTypeEnum.SHUTTER, with_state=False)
    _LOGGER.info(f"Devices found : {list_devices}")

    my_device = list_devices[MY_SHUTTER_ID]
    _LOGGER.info(f"My device found {MY_SHUTTER_ID} : {my_device}")
    assert my_device['name'] == 'Test'
    assert my_device['type'] == DeviceTypeEnum.SHUTTER

    # get shutter position
    list_pos = await client.get_status_details([MY_SHUTTER_ID])
    _LOGGER.info(f"Positions found : {list_pos}")

    _LOGGER.info("---------- Moving UP ---------")
    await client.move_shutter_direction(MY_SHUTTER_ID, ShutterMoveEnum.UP)

    await asyncio.sleep(10)

    list_pos = await client.get_status_details([MY_SHUTTER_ID])
    _LOGGER.info(f"Positions found after move UP: {list_pos}")

    _LOGGER.info("---------- Moving 75% ---------")
    await client.move_shutter_percentage(MY_SHUTTER_ID, 75)

    await asyncio.sleep(10)

    list_pos = await client.get_status_details([MY_SHUTTER_ID])
    _LOGGER.info(f"Positions found after move 75%: {list_pos}")

    _LOGGER.info("End of integration tests : deconnecting...")

    await client.disconnect()
