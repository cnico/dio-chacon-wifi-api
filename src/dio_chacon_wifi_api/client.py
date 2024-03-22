# -*- coding: utf-8 -*-
"""Client for the DIO Chacon wifi API."""
import asyncio
import logging
from typing import Any

from .const import DeviceTypeEnum
from .const import ShutterMoveEnum
from .exceptions import DIOChaconAPIError
from .session import DIOChaconClientSession

_LOGGER = logging.getLogger(__name__)


class DIOChaconAPIClient:
    """Proxy to the DIO Chacon wifi API."""

    def __init__(self, login_email: str, password: str, installation_id: str = "noid") -> None:
        """Initialize the API and authenticate so we can make requests.

        Args:
            email: string containing your email in DIO app
            password: string containing your password in DIO app
            installation_id: a given unique id defining the client side installation
        """
        self._login_email = login_email
        self._password = password
        self._installation_id = installation_id
        self._session: DIOChaconClientSession | None = None
        self._id = 0
        self._messages_connection_queue: asyncio.Queue = asyncio.Queue()
        self._messages_responses_queue: asyncio.Queue = asyncio.Queue()

    async def _get_session(self) -> DIOChaconClientSession:
        if self._session is None:

            _LOGGER.debug("Session creation via _get_session()")

            self._session = DIOChaconClientSession(
                self._login_email, self._password, self._installation_id, self._message_received_callback
            )

            await self._session.login()
            await self._session.ws_connect()

            # Wait for the reception of the connection success message from the server.
            try:
                asyncio.wait_for(self._messages_connection_queue.get(), 10)
            except TimeoutError:
                _LOGGER.error("Error connecting to the server !")
                raise DIOChaconAPIError("No connection aknowledge message received from the server !")

        return self._session

    def _message_received_callback(self, data: Any) -> None:
        """The callback called whenever a server side message is received.
        Args:
            data: the message which is a from json converted dict.
        """
        _LOGGER.debug("Callback Websocket received data %s", data)

        if "name" in data and data["name"] == "connection" and data["action"] == "success":
            # Sends the connection message in the dedicated queue
            self._messages_connection_queue.put_nowait(data)
            return

        if "id" in data:
            # Sends the response message which has the same id has the request
            self._messages_responses_queue.put_nowait(data)
            return

        # TODO : manage messages that are state changes pushed from the server...

        _LOGGER.warn("Unknown message received : %s", data)

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

        _LOGGER.debug(f"WS request to send = {msg}")
        await self._get_session()
        await self._session.ws_send_message(msg)

        raw_results = await self._messages_responses_queue.get()
        if raw_results["id"] != req_id:
            _LOGGER.error("The received message does not have a correct id. %s", raw_results)
            raise DIOChaconAPIError("Unexpected message order with incorrect id !")

        return raw_results

    async def disconnect(self) -> None:
        if self._session:
            # Send a disconnect message to the server
            await self._send_ws_message("POST", "/session/logout", {})

            # Close the web socket
            await self._session.ws_disconnect()

    async def get_user_id(self) -> str:
        """Search for the user id

        Returns:
            A string for the unique user id from the server.
        """

        raw_results = await self._send_ws_message("GET", "/user", {})

        return raw_results["data"]["id"]

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
