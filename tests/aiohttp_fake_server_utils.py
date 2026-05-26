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

INVALID_PASSWORD = "PASS_INVALID_AUTH"


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
        if INVALID_PASSWORD in (await request.text()):
            _LOGGER.debug("MOCK server. Response with fake invalid authentication")
            return web.json_response(body='{"status":400,"data":"Invalid username/password."}', status=200)
        else:
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
                # Add one switch
                response["data"].append({})
                response["data"][1]["id"] = "L4HActuator_idmock2"
                response["data"][1]["name"] = "Shutter mock 2"
                response["data"][1]["type"] = ".dio1.wifi.genericSwitch.switch."
                response["data"][1]["modelName"] = "CERNwd-3B"
                response["data"][1]["softwareVersion"] = "1.0.4"
                # Add one unknown device
                response["data"].append({})
                response["data"][2]["id"] = "L4HActuator_idmock3"
                response["data"][2]["name"] = "Shutter mock 3 unknown"
                response["data"][2]["type"] = ".dio1.camera.unknown"
                response["data"][2]["modelName"] = "CERNwd-3B"
                response["data"][2]["softwareVersion"] = "X.0.X"
                # Add one doorbell
                response["data"].append({})
                response["data"][3]["id"] = "Tuya_idmock4"
                response["data"][3]["name"] = "Doorbell mock 4"
                response["data"][3]["type"] = ".wifi.doorBell.camera.videostream."
                response["data"][3]["modelName"] = "DIOVDP-B03"
                response["data"][3]["softwareVersion"] = "Wifi: 1.1.2, MCU: 1.1.2"

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
                response["data"]["Tuya_idmock4"] = {}
                response["data"]["Tuya_idmock4"]["rc"] = 1
                response["data"]["Tuya_idmock4"]["links"] = list()
                response["data"]["Tuya_idmock4"]["links"].append({})
                response["data"]["Tuya_idmock4"]["links"][0]["rt"] = "gw.r.lastEvent"
                response["data"]["Tuya_idmock4"]["links"][0]["type"] = "ring"
                response["data"]["Tuya_idmock4"]["links"][0]["ts"] = "2026-05-22T08:20:08.667Z"
                response["data"]["Tuya_idmock4"]["links"][0]["data"] = {
                    "reason": None,
                    "image": "https://mock.example.com/ring.jpeg",
                }

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


async def pump_push_queue(ws: aiohttp.web_ws.WebSocketResponse, push_queue: Queue) -> None:
    while not ws.closed:
        message = await push_queue.get()
        _LOGGER.debug("MOCK Server WS : pushing queued message. %s", message)
        await ws.send_str(json.dumps(message))
        push_queue.task_done()


async def websocket_handler(request: web.Request, recording_queue: Queue, push_queue: Queue | None = None):
    _LOGGER.debug('MOCK Server WS : Websocket connection starting')
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    _LOGGER.debug('MOCK Server WS : Websocket connection ready')
    if request.query.get("password") == INVALID_PASSWORD:
        _LOGGER.debug('MOCK Server WS : Sending invalid auth for connection failure')
        await ws.send_str('{"name":"connection","action":"invalid","data":""}')
    else:
        _LOGGER.debug('MOCK Server WS : Sending connection success')
        await ws.send_str('{"name":"connection","action":"success","data":""}')

    pump_task = asyncio.create_task(pump_push_queue(ws, push_queue)) if push_queue is not None else None

    await asyncio.create_task(websocket_messages_handler(ws, recording_queue))

    if pump_task is not None:
        pump_task.cancel()
        try:
            await pump_task
        except asyncio.CancelledError:
            pass

    return ws


async def run_fake_http_server(aiohttp_server, recording_queue: Queue, push_queue: Queue | None = None) -> None:

    _LOGGER.debug("Starting Mock server...")

    app = web.Application()

    call = partial(endpoint, recording_queue=recording_queue)
    call_ws = partial(websocket_handler, recording_queue=recording_queue, push_queue=push_queue)
    app.add_routes([web.route("*", "/api/{tail:.*}", call), web.route("*", "/ws", call_ws)])

    await aiohttp_server(app, port=MOCK_PORT)
