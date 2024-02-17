# -*- coding: utf-8 -*-
"""Client for the DIO Chacon wifi API."""
import logging
from typing import Any

from .const import DeviceTypeEnum
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

    async def disconnect(self) -> None:
        if self._session:
            await self._session.ws_disconnect()

    async def search_all_ids(self) -> Any:
        """Search

        Returns:
            A list of tuples composed of id and type.
        """

        req_id = self._get_next_id()

        msg = {}
        msg["method"] = "GET"
        msg["path"] = "/device"
        msg["parameters"] = {}
        msg["id"] = req_id

        _LOGGER.debug(f"request = {msg}")
        await (await self._get_session()).ws_send_message(msg)

        raw_results = await (await self._get_session()).ws_receive_msg()
        _LOGGER.debug(f"raw_results = {raw_results}")

        results = []
        for device in raw_results["data"]:
            result = {}
            result["id"] = device["id"]
            result["name"] = device["name"]
            result["type"] = DeviceTypeEnum(device["type"]).name  # Converts type to our constant definition
            results.append(result)

        # _LOGGER.debug(f"results = {results}")

        return results
