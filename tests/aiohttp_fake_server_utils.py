# -*- coding: utf-8 -*-
"""Http server mocking requests/responses for test_client.py.
Inspired from : https://gist.github.com/ex3cv/2bbbbaf748c604fd737e1bb8372336e7
"""
import asyncio
import json
import logging
from asyncio import Queue
from functools import partial

import aiohttp
from aiohttp import web

_LOGGER = logging.getLogger(__name__)

MOCK_PORT = 38080


async def endpoint(
    request: web.Request,
    recording_queue: Queue,
) -> web.Response:

    _LOGGER.debug("MOCK server. Request received = %s", request)
    for_assertions = {}
    for_assertions["method"] = request.method
    for_assertions["rel_url"] = str(request.rel_url)
    for_assertions["body"] = str(await request.text())

    # record request for future inspection
    await recording_queue.put(for_assertions)
    if str(request.rel_url).startswith("/api/session/login"):
        _LOGGER.debug("MOCK server. Response with fake session token")
        return web.json_response(body='{"status":200,"data":{"sessionToken":"r:myfakesessionToken"}}', status=200)

    _LOGGER.debug("MOCK server. Response None")
    return None


async def websocket_messages_handler(ws: aiohttp.web_ws.WebSocketResponse):
    async for msg in ws:
        _LOGGER.debug("MOCK Server WS : received message : %s", msg)
        if msg.type == aiohttp.WSMsgType.TEXT:

            content = json.loads(msg.data)
            path = content["path"]
            id = content["id"]

            if path == "/user":
                response = {}
                response["id"] = id
                response["status"] = 200
                response["data"] = {}
                response["data"]["id"] = "mocked-user-id"
                response["data"]["name"] = "mocked-user-name"
                _LOGGER.debug("MOCK Server WS : response /user to send. %s", response)
                await ws.send_str(json.dumps(response))

            if path == "/session/logout":
                response = {}
                response["id"] = id
                response["status"] = 200
                response["name"] = "disconnection"
                response["action"] = "success"
                await ws.send_str(json.dumps(response))
                await ws.close()
                break

    _LOGGER.debug('MOCK Server WS : Websocket connection closed')


async def websocket_handler(request: web.Request):
    _LOGGER.debug('MOCK Server WS : Websocket connection starting')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    _LOGGER.debug('MOCK Server WS : Websocket connection ready')
    await ws.send_str('{"name":"connection","action":"success","data":""}')
    await asyncio.create_task(websocket_messages_handler(ws))

    return ws


async def run_fake_http_server(aiohttp_server, recording_queue: Queue) -> None:

    _LOGGER.debug("Starting Mock server...")

    app = web.Application()

    call = partial(endpoint, recording_queue=recording_queue)
    app.add_routes([web.route("*", "/api/{tail:.*}", call), web.route("*", "/ws", websocket_handler)])

    await aiohttp_server(app, port=MOCK_PORT)
