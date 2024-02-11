# coding: utf-8
"""Integration tests for DIO Chacon wifi api."""
import pytest

import logging

from dio_chacon_wifi_api import DIOChaconAPIClient

# Enter correct real values here for the tests to complete successfully with real Flipr Server calls.

USERNAME=""
PASSWORD=""
MY_SHUTTER_ID=""

logging.basicConfig(level=logging.DEBUG)

_LOGGER = logging.getLogger(__name__)

# @pytest.mark.skip("Not an automated test but an example of usage with real values.")
@pytest.mark.asyncio
async def test_integration_simple() -> None:
    """ Connect then lists all the devices. """

    # Init client
    client = DIOChaconAPIClient(USERNAME, PASSWORD)

    list_ids = await client.search_all_ids()
    _LOGGER.info(f"Identifiants trouvés : {list_ids}")

    # TODO assert MY_SHUTTER_ID in list_fliprs

    await client.disconnect()
