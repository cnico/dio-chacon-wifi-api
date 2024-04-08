# Dio Chacon Wifi API

[![PyPi](https://img.shields.io/pypi/v/dio-chacon-wifi-api)](https://pypi.org/project/dio-chacon-wifi-api)
[![GitHub Release](https://img.shields.io/github/release/cnico/dio-chacon-wifi-api.svg)](https://github.com/cnico/dio-chacon-wifi-api/releases)
[![Python Version](https://img.shields.io/pypi/pyversions/dio-chacon-wifi-api)](https://pypi.org/project/dio-chacon-wifi-api/)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Read the docs](https://img.shields.io/readthedocs/dio-chacon-wifi-api/latest.svg?label=Read%20the%20Docs)](https://dio-chacon-wifi-api.readthedocs.io/)
[![Codecov](https://codecov.io/gh/cnico/dio-chacon-wifi-api/branch/main/graph/badge.svg)](https://codecov.io/gh/cnico/dio-chacon-wifi-api)
[![Github Activity](https://img.shields.io/github/commit-activity/y/cnico/dio-chacon-wifi-api.svg)](https://github.com/cnico/dio-chacon-wifi-api/commits/main)

DIO Chacon are devices mainly distributed in the European market.
Chacon provide various device to control lights, shutters, camera, etc.
The website contains it all : [https://chacon.com/](https://chacon.com/)

The cool thing about their device is that they have RF (433Mhz, used by remote control in house) and Wifi protocols (used by the mobile App).

The wifi protocol is cloud based with their server and quite reactive through permanent connections (via websockets).

This project is a simple implementation, based on the Wifi protocol, of a python client to give the possibility to connect and acts on the devices. It currently supports lights and shutters. It can lists all registered devices (via the mobile app), get their status (on/off ; open level) and act on them (switch on/off ; move up/down/stop cover or move a given percentage of openess).

It is used in a [HomeAssistant](<https://home-assistant.io/>) integration but is also usable in other automation platforms (jeedom, etc).

## Using this library

To implement a client that interact with Chacon devices, simply have look at [test_integrations_light.py](https://github.com/cnico/dio-chacon-wifi-api/blob/main//tests/test_integrations_light.py) or [test_integrations_shutter.py](https://github.com/cnico/dio-chacon-wifi-api/blob/main//tests/test_integrations_shutter.py) that provide effective implementations.

The library is published in [pypi.org](https://pypi.org/) and so can be very easily used in any python project (with python > 3.10).

`pip install dio-chacon-wifi-api`

Note that after the first API call, the connection to the chacon's cloud server is a open in a form of a websocket. To close it, you have to call disconnect method.

Note also that this client has auto reconnection implemented in case of a network temporary failure for example.

## Contributing to this project

If you find bugs or want to improve the library, simply open an issue and propose PR to merge.
Chacon have lots of devices that could be managed via this library.

## Design principles

The wifi protocol is described in [Protocol.md](https://github.com/cnico/dio-chacon-wifi-api/blob/main/Protocol.md).
You can test this protocol manually through postman with establishing a connection via correct authentification (email + password of your chacon mobile app account) ; then upgrade the connection to Websocket and then interact with json messages in the Websocket stream.

For the implementation of the library, it is based on the great [aiohttp](https://docs.aiohttp.org/) library that we use as a http client for REST requests and websocket exchange.
All the library is asynchronous and based on [asyncio](https://docs.python.org/3/library/asyncio-dev.html).

The websocket permanent connection is established lazily when it is necessary (for example for devices discovery) by an asyncio task. This tasks keeps the connection permanent via automatic ping/pong messages.
The protocol is based two types of interaction :

- Requests / Responses : this is handled via json message sent in the websocket with an id (the library automatically manages this id) and a response received from the server that has the same id has the request.
- Server side sent messages : these push messages (for example a light manually swithed on/off with the button or other event) are sent back to the registerer callback method when you initialize the client.
