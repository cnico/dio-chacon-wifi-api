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
    for_assertions["protocol"] = "HTTP"
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


async def websocket_messages_handler(ws: aiohttp.web_ws.WebSocketResponse, recording_queue: Queue):
    async for msg in ws:
        _LOGGER.debug("MOCK Server WS : received message : %s", msg)
        if msg.type == aiohttp.WSMsgType.TEXT:

            content = json.loads(msg.data)
            path = content["path"]
            id = content["id"]

            for_assertions = {}
            for_assertions["protocol"] = "WS"
            for_assertions["method"] = content["method"]
            for_assertions["parameters"] = content["parameters"]
            for_assertions["path"] = path
            for_assertions["id"] = id
            # record request for future inspection
            await recording_queue.put(for_assertions)

            if path == "/user":
                response = {}
                response["id"] = id
                response["status"] = 200
                response["data"] = {}
                response["data"]["id"] = "mocked-user-id"
                response["data"]["name"] = "mocked-user-name"
                _LOGGER.debug("MOCK Server WS : response /user to send. %s", response)
                await ws.send_str(json.dumps(response))

            if path == "/device":
                response = {}
                response["id"] = id
                response["status"] = 200
                response["data"] = list()
                # Add one shutter
                response["data"].append({})
                response["data"][0]["id"] = "L4HActuator_idmock1"
                response["data"][0]["name"] = "Shutter mock 1"
                response["data"][0]["type"] = ".dio1.wifi.shutter.mvt_linear."
                response["data"][0]["modelName"] = "CERSwd-3B"
                response["data"][0]["softwareVersion"] = "1.0.6"
                # Add one light
                response["data"].append({})
                response["data"][1]["id"] = "L4HActuator_idmock2"
                response["data"][1]["name"] = "Shutter mock 2"
                response["data"][1]["type"] = ".dio1.wifi.genericSwitch.switch."
                response["data"][1]["modelName"] = "CERNwd-3B"
                response["data"][1]["softwareVersion"] = "1.0.4"

                _LOGGER.debug("MOCK Server WS : response /device to send. %s", response)
                await ws.send_str(json.dumps(response))

            if path == "/device/states":
                response = {}
                response["id"] = id
                response["status"] = 200
                response["data"] = {}
                response["data"]["L4HActuator_idmock1"] = {}
                response["data"]["L4HActuator_idmock1"]["rc"] = 1
                response["data"]["L4HActuator_idmock1"]["links"] = list()
                response["data"]["L4HActuator_idmock1"]["links"].append({})
                response["data"]["L4HActuator_idmock1"]["links"][0]["rt"] = "oic.r.openlevel"
                response["data"]["L4HActuator_idmock1"]["links"][0]["openLevel"] = 75
                response["data"]["L4HActuator_idmock1"]["links"].append({})
                response["data"]["L4HActuator_idmock1"]["links"][1]["rt"] = "oic.r.movement.linear"
                response["data"]["L4HActuator_idmock1"]["links"][1]["movement"] = "stop"
                response["data"]["L4HActuator_idmock2"] = {}
                response["data"]["L4HActuator_idmock2"]["rc"] = 1
                response["data"]["L4HActuator_idmock2"]["links"] = list()
                response["data"]["L4HActuator_idmock2"]["links"].append({})
                response["data"]["L4HActuator_idmock2"]["links"][0]["rt"] = "oic.r.switch.binary"
                response["data"]["L4HActuator_idmock2"]["links"][0]["value"] = 0

                _LOGGER.debug("MOCK Server WS : response /device/states to send. %s", response)
                await ws.send_str(json.dumps(response))

            if path == "/device/L4HActuator_idmock1/action/mvtlinear":
                response = {}
                response["id"] = id
                response["status"] = 200

                _LOGGER.debug(
                    "MOCK Server WS : response /device/L4HActuator_idmock1/action/mvtlinear to send. %s", response
                )
                await ws.send_str(json.dumps(response))

                # simulates asynchronous send then send a status message for callback server side event
                async def coro_callback():
                    await asyncio.sleep(0.200)
                    response = {}
                    response["name"] = "deviceState"
                    response["action"] = "update"
                    response["data"] = {}
                    response["data"]["di"] = "L4HActuator_idmock1"
                    response["data"]["rc"] = 1
                    response["data"]["links"] = list()
                    response["data"]["links"].append({})
                    response["data"]["links"][0]["rt"] = "oic.r.openlevel"
                    response["data"]["links"][0]["openLevel"] = 69
                    response["data"]["links"].append({})
                    response["data"]["links"][1]["rt"] = "oic.r.movement.linear"
                    response["data"]["links"][1]["movement"] = "down"
                    _LOGGER.debug("MOCK Server WS : callback status to send. %s", response)
                    await ws.send_str(json.dumps(response))

                asyncio.create_task(coro_callback())

            if path == "/device/L4HActuator_idmock1/action/openlevel":
                response = {}
                response["id"] = id
                response["status"] = 200

                _LOGGER.debug(
                    "MOCK Server WS : response /device/L4HActuator_idmock1/action/openlevel to send. %s", response
                )
                await ws.send_str(json.dumps(response))

                # simulates asynchronous send then send a status message for callback server side event
                async def coro_callback():
                    await asyncio.sleep(0.200)
                    response = {}
                    response["name"] = "deviceState"
                    response["action"] = "update"
                    response["data"] = {}
                    response["data"]["di"] = "L4HActuator_idmock1"
                    response["data"]["rc"] = 1
                    response["data"]["links"] = list()
                    response["data"]["links"].append({})
                    response["data"]["links"][0]["rt"] = "oic.r.openlevel"
                    response["data"]["links"][0]["openLevel"] = 69
                    response["data"]["links"].append({})
                    response["data"]["links"][1]["rt"] = "oic.r.movement.linear"
                    response["data"]["links"][1]["movement"] = "down"
                    _LOGGER.debug("MOCK Server WS : callback status to send. %s", response)
                    await ws.send_str(json.dumps(response))

                asyncio.create_task(coro_callback())

            if path == "/device/L4HActuator_idmock2/action/switch":
                response = {}
                response["id"] = id
                response["status"] = 200

                _LOGGER.debug(
                    "MOCK Server WS : response /device/L4HActuator_idmock2/action/switch to send. %s", response
                )
                await ws.send_str(json.dumps(response))

                # simulates asynchronous send then send a status message for callback server side event
                async def coro_callback():
                    await asyncio.sleep(0.200)
                    response = {}
                    response["name"] = "deviceState"
                    response["action"] = "update"
                    response["data"] = {}
                    response["data"]["di"] = "L4HActuator_idmock2"
                    response["data"]["rc"] = 1
                    response["data"]["links"] = list()
                    response["data"]["links"].append({})
                    response["data"]["links"][0]["rt"] = "oic.r.switch.binary"
                    response["data"]["links"][0]["value"] = 1
                    _LOGGER.debug("MOCK Server WS : callback status to send. %s", response)
                    await ws.send_str(json.dumps(response))

                asyncio.create_task(coro_callback())

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


async def websocket_handler(request: web.Request, recording_queue: Queue):
    _LOGGER.debug('MOCK Server WS : Websocket connection starting')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    _LOGGER.debug('MOCK Server WS : Websocket connection ready')
    await ws.send_str('{"name":"connection","action":"success","data":""}')
    await asyncio.create_task(websocket_messages_handler(ws, recording_queue))

    return ws


async def run_fake_http_server(aiohttp_server, recording_queue: Queue) -> None:

    _LOGGER.debug("Starting Mock server...")

    app = web.Application()

    call = partial(endpoint, recording_queue=recording_queue)
    call_ws = partial(websocket_handler, recording_queue=recording_queue)
    app.add_routes([web.route("*", "/api/{tail:.*}", call), web.route("*", "/ws", call_ws)])

    await aiohttp_server(app, port=MOCK_PORT)
