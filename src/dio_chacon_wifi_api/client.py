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

    def __init__(
        self, login_email: str, password: str, installation_id: str = "noid", callback_device_state=None
    ) -> None:
        """Initialize the API and authenticate so we can make requests.

        Args:
            email: string containing your email in DIO app
            password: string containing your password in DIO app
            installation_id: a given unique id defining the client side installation
        """
        self._login_email = login_email
        self._password = password
        self._installation_id = installation_id
        self._callback_device_state = callback_device_state
        self._session: DIOChaconClientSession | None = None
        self._id = 0
        self._messages_connection_queue: asyncio.Queue = asyncio.Queue()
        self._messages_responses_queue: asyncio.Queue = asyncio.Queue()
        self._messages_buffer: dict = dict()

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
                await asyncio.wait_for(self._messages_connection_queue.get(), 10)
                # Do nothing of the connection successful message.
                self._messages_connection_queue.task_done()
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

        if "name" in data and data["name"] == "deviceState" and data["action"] == "update":
            # Sends the device state pushed from the server to the calling client
            if self._callback_device_state:
                # Sends only pertinent data :
                result = {}
                device_data = data["data"]
                result["id"] = device_data["di"]
                result["connected"] = device_data["rc"] == 1
                for link in device_data["links"]:
                    if link['rt'] == "oic.r.openlevel":
                        result["openlevel"] = link["openLevel"]
                    if link['rt'] == "oic.r.movement.linear":
                        result["movement"] = link["movement"]
                    if link['rt'] == "oic.r.switch.binary":
                        result["is_on"] = link["value"] == 1
                self._callback_device_state(result)
                return
            else:
                _LOGGER.warning("No callback for device state notification ! You shoud implement one.")

        _LOGGER.warning("Unknown message received and dropped : %s", data)

    def _get_next_id(self) -> int:
        self._id = self._id + 1
        return self._id

    async def _consume_message_queue_and_cache_it(self) -> None:
        while not self._messages_responses_queue.empty():
            data = await self._messages_responses_queue.get()
            msg_id: int = int(data["id"])
            cached = self._messages_buffer.get(msg_id)
            if not cached:
                self._messages_buffer[msg_id] = data
            self._messages_responses_queue.task_done()

    async def _get_message_response_with_id(self, message_id: int) -> Any:

        await self._consume_message_queue_and_cache_it()
        cached = self._messages_buffer.get(message_id)
        # Try another after a small sleep
        if not cached:
            await asyncio.sleep(0.5)
            await self._consume_message_queue_and_cache_it()

        cached = self._messages_buffer.get(message_id)
        if not cached:
            _LOGGER.error("No response received for message id : %s", message_id)
            raise DIOChaconAPIError("Unexpected situation : no response with correct id !")

        # Remove value from cache has it is considered as consumed
        self._messages_buffer.pop(message_id)

        _LOGGER.debug("Messages buffer in memory cached size = %s", len(self._messages_buffer))

        return cached

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

        raw_results = await self._get_message_response_with_id(req_id)

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

    async def search_all_devices(self, device_type_to_search: DeviceTypeEnum = None, with_state: bool = False) -> dict:
        """Search all the known devices with their states : positions for shutters and on/off for lights

        Args:
            device_type_to_search: the device type to search for. None means to return all type (SHUTTERS and LIGHTS)
            with_state: True to return the detailed states like shutter position and light on or off.

        Returns:
            A list of tuples composed of id, name, type, openlevel and movement for shutter, is_on for light.
        """

        raw_results = await self._send_ws_message("GET", "/device", {})

        results = dict()
        ids = []
        for device in raw_results["data"]:
            result = {}
            id = device["id"]
            type = device["type"]
            if not device_type_to_search or device_type_to_search.equals(type):
                ids.append(id)
                result["id"] = id
                result["name"] = device["name"]
                result["type"] = DeviceTypeEnum.from_dio_api(type)  # Converts type to our constant definition
                result["model"] = device["modelName"] + "_" + device["softwareVersion"]
                results[id] = result

        if with_state:
            details = await self.get_status_details(ids)
            for id in ids:
                results[id]["connected"] = details[id]["connected"]
                if "openlevel" in details[id]:
                    results[id]["openlevel"] = details[id]["openlevel"]
                    results[id]["movement"] = details[id]["movement"]
                if "is_on" in details[id]:
                    results[id]["is_on"] = details[id]["is_on"]

        return results

    async def get_status_details(self, ids: list) -> dict:
        """Retrieves the status detailed of devices ids given

        Args:
            ids: the device ids to search details for.

        Returns:
            A list of tuples composed of id, connected ; openlevel and movement for shutter, is_on for light.
        """

        parameters = {'devices': ids}
        raw_results = await self._send_ws_message("POST", "/device/states", parameters)

        results = dict()
        for device_key in raw_results['data']:
            device_data = raw_results['data'][device_key]

            result = {}
            result["id"] = device_key
            result["connected"] = device_data["rc"] == 1
            for link in device_data["links"]:
                if link['rt'] == "oic.r.openlevel":
                    result["openlevel"] = link["openLevel"]
                if link['rt'] == "oic.r.movement.linear":
                    result["movement"] = link["movement"]
                if link['rt'] == "oic.r.switch.binary":
                    result["is_on"] = link["value"] == 1
            results[device_key] = result
        return results

    async def move_shutter_direction(self, shutter_id: str, direction: ShutterMoveEnum):
        parameters = {'movement': direction.value.lower()}
        await self._send_ws_message("POST", f"/device/{shutter_id}/action/mvtlinear", parameters)

    async def move_shutter_percentage(self, shutter_id: str, openlevel: int):
        parameters = {'openLevel': openlevel}
        await self._send_ws_message("POST", f"/device/{shutter_id}/action/openlevel", parameters)

    async def switch_light(self, switch_id: str, set_on: bool):
        val = 1 if set_on else 0
        parameters = {'value': val}
        await self._send_ws_message("POST", f"/device/{switch_id}/action/switch", parameters)
