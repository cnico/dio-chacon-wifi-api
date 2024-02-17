# -*- coding: utf-8 -*-
"""Session manager for the DIO Chacon wifi API in order to maintain authentication token between calls.
And context between the various websockets calls."""

from .const import DIOCHACON_AUTH_URL
from .const import DIOCHACON_WS_URL

import json
import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class DIOChaconClientSession:
    """HTTP session manager for DIO Chacon API.

    This session object allows to manage the authentication
    in the API using a token.
    """

    _sessionToken: str = None
    _aiohttp_session: aiohttp.ClientSession | None = None
    _websocket: aiohttp.ClientWebSocketResponse | None = None

    def __init__(self, login_email: str, password: str) -> None:
        """Initialize and authenticate.

        Args:
            username: the flipr registered user
            password: the flipr user's password
        """
        self._login_email = login_email
        self._password = password

    async def login(self) -> None:
        data = {}
        data["email"] = self._login_email
        data["password"] = self._password
        data["installationId"] = "noid"
        payload_data = json.dumps(data)

        # Authenticate with user and pass and store bearer token
        headers_token = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        async def on_request_start(session, trace_config_ctx, params):
            _LOGGER.debug(f"aiohttp request start : {params}")

        async def on_request_chunk_sent(session, trace_config_ctx, params):
            _LOGGER.debug(f"aiohttp request chunk sent : {params}")

        async def on_response_chunk_received(session, trace_config_ctx, params):
            _LOGGER.debug(f"aiohttp response chunk received : {params}")

        async def on_request_end(session, trace_config_ctx, params):
            _LOGGER.debug(f"aiohttp request end : {params}")

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        trace_config.on_request_chunk_sent.append(on_request_chunk_sent)
        trace_config.on_response_chunk_received.append(on_response_chunk_received)

        self._aiohttp_session = aiohttp.ClientSession(trace_configs=[trace_config])
        async with self._aiohttp_session.post(url=DIOCHACON_AUTH_URL, data=payload_data, headers=headers_token) as resp:
            resp_json = await resp.json()
            self._sessionToken = str(resp_json["data"]["sessionToken"])
            _LOGGER.debug("SessionToken of authentication : " + self._sessionToken)

    async def ws_connect(self) -> None:
        """Make a connection to the server via websocket protocol."""
        url = DIOCHACON_WS_URL + "?sessionToken=" + self._sessionToken

        # Simply keep the websocket object for further usage.
        self._websocket = await self._aiohttp_session.ws_connect(url=url, autoping=True)

    async def ws_disconnect(self) -> None:
        await self._websocket.close()
        await self._aiohttp_session.close()

    async def ws_send_message(self, msg) -> None:
        """Sends a message in the websocket by converting it to json.

        Args:
            msg: the message to be sent
        """
        await self._websocket.send_str(json.dumps(msg))

    async def ws_receive_msg(self):
        return await self._websocket.receive_json()
