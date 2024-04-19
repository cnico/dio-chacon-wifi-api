# -*- coding: utf-8 -*-
"""Client for the DIO Chacon wifi API."""
import asyncio
import logging
from asyncio import Lock
from asyncio import Queue
from typing import Any

from .const import DeviceTypeEnum
from .const import DIOCHACON_AUTH_URL
from .const import DIOCHACON_WS_URL
from .const import ShutterMoveEnum
from .const import SwitchOnOffEnum
from .exceptions import DIOChaconAPIError
from .session import DIOChaconClientSession

_LOGGER = logging.getLogger(__name__)


class DIOChaconAPIClient:
    """Client to the DIO Chacon wifi API.
    It is mainly a proxy to the chacon's cloud server.
    It manages authentication, the protocol through the websocket connection and server side callback events.
    """

    def __init__(
        self, login_email: str, password: str, installation_id: str = "noid", callback_device_state: callable = None
    ) -> None:
        """Initialize the client API. Actually do nothing but storing informations.
        The effective authentication and connection are lazyly achieved.

        Parameters:
            login_email: string containing your email in DIO app
            password: string containing your password in DIO app
            installation_id: a given unique id defining the client side installation
            callback_device_state: the callback method that will be called for server side events
        """
        self._login_email: str = login_email
        self._password: str = password
        self._installation_id: str = installation_id
        self._callback_device_state: callable = callback_device_state
        self._session: DIOChaconClientSession | None = None
        # Unique message id for request / response correlation
        self._id: int = 0
        # Queue to await connection response from server
        self._messages_connection_queue: Queue = Queue()
        # Queue to await responses for queries
        self._messages_responses_queue: Queue = Queue()
        # In case of server responses concurrency, uses this buffer to find correct message id response.
        self._messages_buffer: dict = dict()
        # Lock to prevent initialisation of WS connection concurrently
        self._init_lock: Lock = Lock()
        self._auth_url: str = DIOCHACON_AUTH_URL
        self._ws_url: str = DIOCHACON_WS_URL

    def _set_server_urls(self, auth_url: str, ws_url: str) -> None:
        # Simple method to easily mock the server url.
        self._auth_url = auth_url
        self._ws_url = ws_url

    async def _get_or_init_session(self) -> None:
        if self._session and self._session.is_disconnected():
            _LOGGER.warning("You have been disconnected. Automatic reconnection...")
            self._session = None
        if self._session is None:
            async with self._init_lock:
                if self._session is None:
                    _LOGGER.debug("Session creation via init_session")

                    session = DIOChaconClientSession(
                        self._login_email, self._password, self._installation_id, self._message_received_callback
                    )
                    session._set_server_urls(self._auth_url, self._ws_url)

                    await session.login()
                    await session.ws_connect()

                    # Wait for the reception of the connection success message from the server.
                    try:
                        await asyncio.wait_for(self._messages_connection_queue.get(), 10)
                        # Do nothing of the connection successful message.
                        self._messages_connection_queue.task_done()
                    except TimeoutError:
                        _LOGGER.error("Error connecting to the server !")
                        raise DIOChaconAPIError("No connection aknowledge message received from the server !")

                    # stores the intialized session once connection is finished
                    # in order to avoid concurrent access before connection is OK.
                    self._session = session
                    _LOGGER.debug("End of session creation via init_session")

    def _message_received_callback(self, data: Any) -> None:
        """The callback called whenever a server side message is received.
        Parameters:
            data: the message which is a from json converted dict.
        """

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
                        result["is_on"] = link["value"] == SwitchOnOffEnum.ON.value
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
        await self._get_or_init_session()
        await self._session.ws_send_message(msg)

        raw_results = await self._get_message_response_with_id(req_id)

        return raw_results

    async def disconnect(self) -> None:
        """Disconnects for the cloud server and properly closes the connection.
        It must be called at the of API usage or before python program ending.

        """
        if self._session:
            # Send a disconnect message to the server
            await self._send_ws_message("POST", "/session/logout", {})

            # Close the web socket
            await self._session.disconnect()

    async def get_user_id(self) -> str:
        """Search for the user technical id based on its authentification elements.

        Returns:
            A string for the unique user id from the server.
        """

        raw_results = await self._send_ws_message("GET", "/user", {})

        return raw_results["data"]["id"]

    async def search_all_devices(
        self, device_type_to_search: list[DeviceTypeEnum] = None, with_state: bool = False
    ) -> dict:
        """Search all the known devices with their states : positions for shutters and on/off for switches

        Parameters:
            device_type_to_search: the device type to search for. None means to return all type (SHUTTERS and SWITCHES)
            with_state: True to return the detailed states like shutter position and switches on or off.

        Returns:
            A list of tuples composed of id, name, type, openlevel and movement for shutter, is_on for switches.
        """

        raw_results = await self._send_ws_message("GET", "/device", {})

        results = dict()
        ids = []
        for device in raw_results["data"]:
            result = {}
            id = device["id"]
            type = device["type"]
            if not device_type_to_search or (DeviceTypeEnum.from_dio_api(type) in device_type_to_search):
                ids.append(id)
                result["id"] = id
                result["name"] = device["name"]
                result["type"] = DeviceTypeEnum.from_dio_api(type).value  # Converts type to our constant definition
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
        """Retrieves the status detailed of devices ids given.

        Parameters:
            ids: the device ids to search details for.

        Returns:
            A list of tuples composed of id, connected ; openlevel and movement for shutter, is_on for switch.
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
                    result["is_on"] = link["value"] == SwitchOnOffEnum.ON.value
            results[device_key] = result
        return results

    async def move_shutter_direction(self, shutter_id: str, direction: ShutterMoveEnum) -> None:
        """Moves the given shutter in the given direction.

        Parameters:
            shutter_id: the device id defining the chosen shutter.
            direction: up, down or stop movement.
        """

        parameters = {'movement': direction.value.lower()}
        await self._send_ws_message("POST", f"/device/{shutter_id}/action/mvtlinear", parameters)

    async def move_shutter_percentage(self, shutter_id: str, openlevel: int) -> None:
        """Moves the given shutter at a given position.

        Parameters:
            shutter_id: the device id defining the chosen shutter.
            openlevel: the open level percentage between 0 and 100.
        """
        parameters = {'openLevel': openlevel}
        await self._send_ws_message("POST", f"/device/{shutter_id}/action/openlevel", parameters)

    async def switch_switch(self, switch_id: str, set_on: bool) -> None:
        """Switches on or off the given switch.

        Parameters:
            switch_id: the device id defining the chosen switch.
            set_on: on or off as desired state.
        """
        val = SwitchOnOffEnum.ON.value if set_on else SwitchOnOffEnum.OFF.value
        parameters = {'value': val}
        await self._send_ws_message("POST", f"/device/{switch_id}/action/switch", parameters)
