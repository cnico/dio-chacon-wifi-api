# -*- coding: utf-8 -*-
"""Client for the DIO Chacon wifi API."""
import logging
from typing import Any

from .const import DeviceTypeEnum
from .const import ShutterMoveEnum
from .session import DIOChaconClientSession

_LOGGER = logging.getLogger(__name__)


class DIOChaconAPIClient:
    """Proxy to the DIO Chacon wifi API."""

    def __init__(self, login_email: str, password: str) -> None:
        """Initialize the API and authenticate so we can make requests.

        Args:
            email: string containing your email in DIO app
            password: string containing your password in DIO app
        """
        self._login_email = login_email
        self._password = password
        self._session: DIOChaconClientSession | None = None
        self._id = 0

    async def _get_session(self) -> DIOChaconClientSession:
        if self._session is None:
            self._session = DIOChaconClientSession(self._login_email, self._password)

            await self._session.login()
            await self._session.ws_connect()
            # Receiption of the connecion success message from the server.
            await self._session.ws_receive_msg()

        return self._session

    def _get_next_id(self) -> int:
        self._id = self._id + 1
        return self._id

    async def _send_ws_message(self, method: str, path: str, parameters: Any) -> Any:
        req_id = self._get_next_id()

        # Constructs the message that will be formated in JSON by the DIOChaconClientSession object
        msg = {}
        msg["method"] = method
        msg["path"] = path
        msg["parameters"] = parameters
        msg["id"] = req_id

        _LOGGER.debug(f"request = {msg}")
        await (await self._get_session()).ws_send_message(msg)

        # TODO : ignore deviceState that has no id and send events for this...

        correlation_id_ok: bool = False
        while not (correlation_id_ok):
            raw_results = await (await self._get_session()).ws_receive_msg()
            _LOGGER.debug(f"raw_results = {raw_results}")
            if "id" in raw_results and raw_results["id"] == req_id:
                correlation_id_ok = True

        return raw_results

    async def disconnect(self) -> None:
        if self._session:
            # Send a disconnect message to the server
            await self._send_ws_message("POST", "/session/logout", {})

            # Close the web socket
            await self._session.ws_disconnect()

    async def search_all_devices(self) -> Any:
        """Search all the known devices

        Returns:
            A list of tuples composed of id, name and type.
        """

        raw_results = await self._send_ws_message("GET", "/device", {})

        results = []
        for device in raw_results["data"]:
            result = {}
            result["id"] = device["id"]
            result["name"] = device["name"]
            result["type"] = DeviceTypeEnum.from_dio_api(device["type"])  # Converts type to our constant definition
            results.append(result)

        return results

    async def get_shutters_positions(self, ids: list) -> Any:

        parameters = {'devices': ids}
        raw_results = await self._send_ws_message("POST", "/device/states", parameters)

        results = []
        for device_key in raw_results['data']:
            device_data = raw_results['data'][device_key]

            result = {}
            result["id"] = device_key
            for link in device_data["links"]:
                if link['rt'] == "oic.r.openlevel":
                    result["openlevel"] = link["openLevel"]
                if link['rt'] == "oic.r.movement.linear":
                    result["movement"] = link["movement"]
            results.append(result)
        return results

    async def move_shutter_direction(self, shutter_id: str, direction: ShutterMoveEnum):
        parameters = {'movement': direction.value.lower()}
        await self._send_ws_message("POST", f"/device/{shutter_id}/action/mvtlinear", parameters)
        # TODO : handle error in response...

    async def move_shutter_percentage(self, shutter_id: str, openlevel: int):
        parameters = {'openLevel': openlevel}
        await self._send_ws_message("POST", f"/device/{shutter_id}/action/openlevel", parameters)
        # TODO : handle error in response...
