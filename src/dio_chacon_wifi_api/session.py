# -*- coding: utf-8 -*-
"""Session manager for the DIO Chacon wifi API in order to maintain authentication token between calls.
And context between the various websockets calls.
Largely inspired by https://github.com/jjlawren/python-plexwebsocket/blob/master/plexwebsocket.py
"""
import asyncio
import json
import logging

import aiohttp

from .exceptions import DIOChaconInvalidAuthError

MAX_FAILED_ATTEMPTS = 5

STATE_CONNECTED = "connected"
STATE_DISCONNECTED = "disconnected"
STATE_STARTING = "starting"
STATE_STOPPED = "stopped"

_LOGGER = logging.getLogger(__name__)


class DIOChaconClientSession:
    """HTTP session manager for DIO Chacon API.

    This session object allows to manage the authentication
    in the API using a token.
    """

    _state: str = None
    _failed_attempts: int = 0
    _sessionToken: str = None
    _aiohttp_session: aiohttp.ClientSession | None = None
    _websocket: aiohttp.ClientWebSocketResponse | None = None
    _listen_task: asyncio.Task | None = None

    def __init__(self, login_email: str, password: str, installation_id: str, callback: callable) -> None:
        """Initialize and authenticate.

        Parameters:
            username: the dio chacon user (mainly the email to log in the app)
            password: the dio chacon user's password
            installation_id: an application id which is an arbitrary string to identify the installation.
            callback (Runnable):
                Called when interesting events occur. Provides arguments:
                   data (str): websocket payload contents deserialized from json
        """
        self._login_email = login_email
        self._password = password
        self._installation_id = installation_id
        self._callback = callback

    def _set_server_urls(self, auth_url: str, ws_url: str) -> None:
        # Simple method to easily mock the server url by overriding default values.
        self._auth_url = auth_url
        self._ws_url = ws_url

    async def login(self) -> None:
        data = {}
        data["email"] = self._login_email
        data["password"] = self._password
        data["installationId"] = self._installation_id
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
        async with self._aiohttp_session.post(url=self._auth_url, data=payload_data, headers=headers_token) as resp:
            resp_json = await resp.json()
            if resp_json["status"] == 400:
                err_msg = resp_json["data"]
                _LOGGER.debug("Invalid auth response received : %s", err_msg)
                await self._aiohttp_session.close()
                raise DIOChaconInvalidAuthError(err_msg)
            self._sessionToken = str(resp_json["data"]["sessionToken"])
            _LOGGER.debug("SessionToken of authentication : " + self._sessionToken)

    async def ws_connect(self) -> None:
        """Make a connection to the server via websocket protocol."""

        # Starts a background parallel task to permanently listen to events
        # sent by the WS server and transfer them via callback.
        self._listen_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Listen to messages"""
        # Infinite loop to listen to messages on the websocket and manage retries.
        self._failed_attempts = 0
        while self._state != STATE_STOPPED:
            await self._running()

    async def _running(self) -> None:
        url = self._ws_url + "?sessionToken=" + self._sessionToken

        self._state = STATE_STARTING

        try:
            async with self._aiohttp_session.ws_connect(url, heartbeat=15, autoping=True) as ws_client:
                self._state = STATE_CONNECTED
                self._failed_attempts = 0
                self._websocket = ws_client
                async for message in ws_client:
                    if self._state == STATE_STOPPED:
                        break

                    if message.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error("Error received from WS server: %s", message)
                        break

                    if message.type == aiohttp.WSMsgType.CLOSED:
                        _LOGGER.warning("AIOHTTP websocket connection closed")
                        break

                    if message.type == aiohttp.WSMsgType.TEXT:
                        _LOGGER.debug("Websocket received data %s", message)
                        msg = message.json()
                        self._callback(msg)

        except aiohttp.ClientResponseError as error:
            _LOGGER.error("Unexpected response received from server : %s", error)
            self._state = STATE_STOPPED
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as error:
            if self._failed_attempts >= MAX_FAILED_ATTEMPTS:
                _LOGGER.error("Too many retries to reconnect to server. Please restart globally.")
                self._state = STATE_STOPPED
            elif self._state != STATE_STOPPED:
                retry_delay = min(2 ** (self._failed_attempts - 1) * 30, 300)
                self._failed_attempts += 1
                _LOGGER.error("Websocket connection failed, retrying in %ds: %s", retry_delay, error)
                self._state = STATE_DISCONNECTED
                await asyncio.sleep(retry_delay)
        except Exception as error:
            if self._state != STATE_STOPPED:
                _LOGGER.exception("Unexpected exception occurred: %s", error)
                self._state = STATE_STOPPED

    async def disconnect(self) -> None:
        self._state = STATE_STOPPED
        if self._websocket:
            await self._websocket.close()
        if self._aiohttp_session:
            await self._aiohttp_session.close()
        # Let the _listen infinite loop terminate correctly with STATE_STOPPED signal.
        await asyncio.sleep(0.5)

    async def ws_send_message(self, msg) -> None:
        """Sends a message in the websocket by converting it to json.

        Parameters:
            msg: the message to be sent
        """
        await self._websocket.send_str(json.dumps(msg))

    def is_disconnected(self) -> bool:
        return self._state == STATE_STOPPED or self._websocket.closed
